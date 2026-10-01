#!/usr/bin/env python3
"""AST checks for pinned K1 seams, without importing the simulator or models."""
import argparse,ast,json,subprocess
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--k1',default='external/k1');a=p.parse_args();root=Path(a.k1)
    tree=ast.parse((root/'src/robo_harness/runtime.py').read_text())
    functions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    params={x.arg for x in functions['run_agent'].args.args}
    assert {'registry_class','client_factory','adapter','max_calls'}.issubset(params)
    classes={n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
    methods={n.name for n in classes['ToolRegistry'].body if isinstance(n,ast.FunctionDef)}
    assert {'observe','schemas','execute'}.issubset(methods)
    print(json.dumps({'run_agent_extension_seams':True,'registry_api':True,
        'revision':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),
        'scope':'source shape only; no native execution or empirical result'},indent=2))
if __name__=='__main__':main()
