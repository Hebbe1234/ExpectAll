import pulp
import pulp.apis







def main():
    print("Hello World!")
    
    A_g = pulp.LpVariable.dicts('A', [(t) for t in range(2)], lowBound=-1, upBound=1, cat='Integer')


if __name__ == "__main__":
    main()

