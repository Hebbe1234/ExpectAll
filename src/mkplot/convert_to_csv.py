import argparse
import os    



def parse_type(x: str):
    if "." in x and x.replace(".","").isnumeric():
        return float(x)
    elif x.isdigit():
        return int(x)
    return x

def get_header_and_rows(dir):
    headers = []
    rows = []
    first = True

    for subdirs, _, files in os.walk(dir):
        for output in files:
            with open(f"{subdirs}/{output}", "r") as f:
                lines = list(map(lambda x: x.strip().lower(), f.readlines()))
                data = lines[-1]
                if "true" not in data and "false" not in data:
                    continue
                if first:
                    headers = lines[-2].split(";")
                    newHeader = headers[0:3]
                    newHeader.extend(["size","solutions"])
                    newHeader.extend(headers[3:])
                    headers = newHeader
                rows.append(list(map(parse_type, data.split(";"))))
    return headers, rows                
    

def convert_to_scatter_format(dir):
    data = {}
    for subdirs, dirs, files in os.walk(dir):
        if not files:
            continue
        header, rows = get_header_and_rows(subdirs)
        if header and rows:
            graph_name = subdirs.split("/")[-1]
            data[graph_name] = (header, rows)
    return data

# if __name__ == "__main__":


    # parser = argparse.ArgumentParser("mainbdd.py")
    # parser.add_argument("-dir", type=str, help="output directory to graph")
    # parser.add_argument("-type", default="scatter", type=str, help="scatter, cactus")
    # args = parser.parse_args()

    # # for x in range(10):
    # #     with open(f"{args.dir}/output{x}.txt", "w") as f:
    # #         f.writelines(["solve_time;all_time;satisfiable;demands;wavelengths","\n",f"{x/2};{x/5};True;{x};{x+20}","\n" ])
    # # exit(0)

    # if args.type == "scatter":
    #     convert_to_scatter_csv(args.dir)
    

