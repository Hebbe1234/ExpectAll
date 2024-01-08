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
                    headers = ["file"] + newHeader
                rows.append([subdirs]+  list(map(parse_type, data.split(";"))))
    return headers, rows                

def get_earliest_termination(rows):
    grouped = {}
    for r in rows:
        file = r[0]
        if file not in grouped:
            grouped[file] = []
        
        grouped[file].append(r[1:])
    
    earliest_termination = {}
    
    for f,rows in grouped.items():
        print("")

        for r in rows:
            if r[2] != 'true':
                continue
            
            print(r)
            
            if f not in earliest_termination:
                earliest_termination[f] = r
                continue
            
            if r[0] < earliest_termination[f][0]:
                earliest_termination[f] = r
                
    return earliest_termination

def output_earliest_termination(outdir, header, earliest_terminations):
    for f in earliest_terminations:
        if not os.path.isdir(f"{outdir}/" + f.split('\\')[-1]):
            os.makedirs(f"{outdir}/" + f.split('\\')[-1])
        with open(f"{outdir}/" + f.split('\\')[-1] + f"/output{earliest_terminations[f][5]}.txt", "w", encoding="cp1252") as out_file:
            out_file.write(";".join(header) + "\n")
            out_file.write(";".join(map(lambda x: "True" if x == "true" else x, map(str, earliest_terminations[f]))) + "\n")
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=str, help="dir to run on")
    parser.add_argument("--out", default="", type=str, help="dir to output to")
    args = parser.parse_args()

    (h, r) = get_header_and_rows(args.dir)
    et = get_earliest_termination(r)
    print({k.split('\\')[-1]:v[6] for k,v in et.items() if v[6] == 7})
    if args.out != "":
        output_earliest_termination(args.out, h[1:], et)
    
    