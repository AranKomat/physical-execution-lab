"""Vectorize source singleton sampling with independent episode RNG streams."""
import numpy as np
from k1lab.errors import ContractError


class Pi05Batch:
    def __init__(self, policy, observation_type):
        import jax
        import jax.numpy as jnp
        from flax import nnx
        if getattr(policy, '_is_pytorch_model', False):
            raise ContractError('this executor binds the released JAX pi0.5 path')
        self.policy = policy
        self.observation_type = observation_type
        self.keys = {}
        self.calls = {}
        self.jax, self.jnp = jax, jnp
        graphdef, self.model_state = nnx.split(policy._model)
        source_method = policy._model.sample_actions.__func__

        def sample(state, key, inputs):
            model = nnx.merge(graphdef, state)
            return source_method(model, key, observation_type.from_dict(inputs), **policy._sample_kwargs)

        # Each mapped row retains the source's inner batch-of-one observation shape.
        # Keep weights dynamic and shared, as source module_jit does. Closing over
        # them in an outer JIT embeds gigabytes of constants in the compiler graph.
        self.sample_batch = jax.jit(jax.vmap(sample, in_axes=(None, 0, 0)))

    def infer(self, episode_ids, raws):
        if (not episode_ids or len(episode_ids) != len(raws)
                or len(set(episode_ids)) != len(episode_ids)):
            raise ContractError('batch requires one unique stable episode ID per input')
        jax, jnp = self.jax, self.jnp
        rows = [self.policy._input_transform(jax.tree.map(lambda x: x, raw)) for raw in raws]
        inputs = jax.tree.map(lambda *x: jnp.stack([jnp.asarray(v)[None, ...] for v in x]), *rows)
        split = [jax.random.split(self.keys.get(idx, jax.random.key(0))) for idx in episode_ids]
        sampling_keys = jnp.stack([pair[1] for pair in split])
        actions = self.sample_batch(self.model_state, sampling_keys, inputs)
        actions.block_until_ready()
        result = np.stack([self.policy._output_transform(dict(
            state=np.asarray(inputs['state'][i, 0]), actions=np.asarray(actions[i, 0])))['actions']
            for i in range(len(episode_ids))]).astype(np.float32)
        if result.shape != (len(episode_ids), 50, 14) or not np.isfinite(result).all():
            raise ContractError('source pi0.5 batch returned invalid H50 joint14 predictions')
        for idx, pair in zip(episode_ids, split):
            self.keys[idx] = pair[0]
            self.calls[idx] = self.calls.get(idx, 0)+1
        clipped = result.copy()
        clipped[:, :, [6,13]] = np.clip(clipped[:, :, [6,13]], 0, 1)
        return dict(actions=clipped, raw_actions=result,
                    episode_ids=list(episode_ids), native_calls_per_episode=dict(self.calls),
                    rng_keys_after={str(idx):jax.random.key_data(key).tolist() for idx,key in self.keys.items()},
                    executor='vmap_source_singleton_sampling', source_batch_numerical_parity_unproven=True)
