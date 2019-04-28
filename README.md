# kami-2-solver
Python solver for Kami2 puzzle game

How to run:

  python solver.py [level]
  
where [level] must be the filename containing the level information in json format (eg: levelData0.json).
  
The solving algorithm is base on https://github.com/erasche/kami-solver, with some more heuristics on how to choose the next move.
