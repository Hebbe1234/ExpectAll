from demands import Demand
import math
class ReducedDemands:
    def __init__(self, demands, reduction_factor, unique_channels, wasted_frequencies, percentage_size_increase, fewer_channels):
        self.demands = demands
        self.reductions_size = reduction_factor
        self.number_of_unique_slots = unique_channels
        self.wasted_frequencies = wasted_frequencies
        self.percentage_total_size_increase = percentage_size_increase
        self.fewer_channels = fewer_channels
    def __str__(self):
        return f"demands reduction {self.reductions_size}, uniqueChannels {self.number_of_unique_slots} waste {self.wasted_frequencies} % {self.percentage_total_size_increase}"
    def __repr__(self):
        return str(self)

def unique_slot_sizes(demands): 
    sizes = []
    for i, d in demands.items(): 
        if d.size not in sizes: 
            sizes.append(d.size)
    return len(sizes)

def get_list_of_smaller_demand_sizes(demands):
    res = []
    original_number_of_channels = unique_slot_sizes(demands)
    for reductionFactor in range(2, 10): 
        loss = 0
        total_size = 0
        new_demands = {}

        for i,d in demands.items(): 
            new_demands[i] = Demand(d.source, d.target, math.ceil(d.size/reductionFactor))
            loss +=  (math.ceil(d.size/reductionFactor)*reductionFactor) - d.size
            total_size += d.size
        k = ReducedDemands(new_demands, reductionFactor, unique_slot_sizes(new_demands), loss, (total_size/100)*loss, original_number_of_channels-unique_slot_sizes(new_demands))
        res.append(k)

    return res

def get_best_reduced_demand_size(demands, highest_alloweed_percentage_increase): 
    res = get_list_of_smaller_demand_sizes(demands)
    best_solution = ReducedDemands(demands, 0, unique_slot_sizes(demands), 0, 0, 0)
    for k in res: 
        if k.fewer_channels > best_solution.fewer_channels and k.percentage_total_size_increase < highest_alloweed_percentage_increase:
            best_solution = k 
        elif k.fewer_channels == best_solution.fewer_channels and k.percentage_total_size_increase < best_solution.percentage_total_size_increase:
            best_solution = k 

    return best_solution

