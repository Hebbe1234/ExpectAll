

import argparse

from RSABuilder import ExpectAllBuilder
from demand_ordering import demand_order_sizes
from topology import get_gravity_demands, get_gravity_demands_no_population, get_nx_graph


if __name__ == "__main__":
   parser = argparse.ArgumentParser("main.py")
   parser.add_argument("--topology", type=str, help="topology to run on")
   parser.add_argument("--seed", default=10, type=int, help="seed to use for random")
   parser.add_argument("--demands", default=5, type=int, help="number of demands")
   parser.add_argument("--max_demand_size", default=30, type=int, help="maximum demand size")
   parser.add_argument("--num_paths",default=2,  type=int, help="number of fixed paths per demand")
   parser.add_argument("--slots",default=320,  type=int, help="number slots")
    
   parser.add_argument('--gapfree', action=argparse.BooleanOptionalAction, help="Build BDD with gapfree")
   parser.add_argument('--upper_bound', action=argparse.BooleanOptionalAction, help="build BDD with upper bound")
   parser.add_argument('--limited', action=argparse.BooleanOptionalAction, help="build BDD with limited")
   parser.add_argument('--all_improvements', action=argparse.BooleanOptionalAction, help="build BDD with gapfree, upper bound and limited")

   parser.add_argument("--k_resilience", default=0, type=int, help="evaluate k link resilience")
   parser.add_argument('--usage', action=argparse.BooleanOptionalAction, help="measure usage")
   parser.add_argument('--draw', default=0, type=int,help="draw the first n RSA solutions in the BDD")

   parser.add_argument("--query", default=0, type=int, help="query 100 times for k links failing")
   parser.add_argument("--query_amount", default=100, type=int, help="how many times to query")
   parser.add_argument('--precomputation', default=0, type=int, help="use precomputation pruning for k links failing")
   
   parser.add_argument('--max_required_slot', action=argparse.BooleanOptionalAction, help="find max required slot")
   
   args = parser.parse_args()
   
   
   G = get_nx_graph(args.topology)
   if G.nodes.get("\\n") is not None:
        G.remove_node("\\n")

   if "japanese_topologies" in args.topology:
      demands = get_gravity_demands(G, args.demands,multiplier=1, seed=args.seed, max_uniform=args.max_demand_size)
   else:
      demands = get_gravity_demands_no_population(G, args.demands,multiplier=1, seed=args.seed, max_uniform=args.max_demand_size)
        
   demands = demand_order_sizes(demands)
   print(demands)
   
   bob = ExpectAllBuilder(G, demands, args.num_paths, slots=args.slots)
   
   if args.gapfree or args.all_improvements:
      bob.sequential()
   
   if args.upper_bound or args.all_improvements:
      bob.set_super_safe_upper_bound()
      
   if args.limited or args.all_improvements:
      bob.safe_limited()
      
   if args.k_resilience > 0:
      bob.use_edge_evaluation(args.k_resilience)
      
   if args.usage:
      bob.output_with_usage()
      
   if args.precomputation > 0:
      bob.failover(args.precomputation)
   
   if args.query > 0:    
      bob.with_querying(args.query, args.query_amount)
      
   bob.construct()
   
   if args.usage:
      print("Usage: ", bob.usage())
   
   if args.k_resilience:
      print(f"{args.k_resilience} link failure resilience: ",  list(bob.edge_evaluation_score())[6])
   
   if args.max_required_slot:
      assert args.precomputation > 0 # Requires some specific k 
      bob.measure_max_required_slot()
      print(f"max required slot for {args.query} or fewer failures:", bob.get_max_required_slot())

   print("Build time: ", bob.get_build_time() + bob.get_failover_build_time())
   
   
   if args.draw > 0:         
      bob.draw(args.draw)
   