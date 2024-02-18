import tarfile
import os 
import re

graph_name_regex = r"(?<=res_)(.*)(?=.gml)"
demand_regex = r"(?<=output)(.*)(?=.txt)"


def parse_path(path):
    def parse_tar_dir(path):
        data = {}
        tar = tarfile.open(path)
        for member in tar.getmembers():
            f = tar.extractfile(member)
            
            if not f:
                continue
            
            lines = f.read().splitlines()
            lines = [l.decode() for l in lines]

            graph_name = re.findall(graph_name_regex, member.name)[0]
            demand = re.findall(demand_regex, member.name)[0]

            if not graph_name in data.keys():
                data.update({graph_name:{}})
            
            data[graph_name][demand] = lines

        return data
            
    def parse_dir(path):
        data = {}

        for root, graph_dirs,files in os.walk(path):
            if not files:
                continue

            for f in files:
                file_path = "".join([root,"/",f])

                with open(file_path, "r") as file:
                    graph_name = re.findall(graph_name_regex, root)[0]
                    demand = re.findall(demand_regex, f)[0]
                    if graph_name not in data.keys():
                        data.update({graph_name:{}})
                    data[graph_name][demand] = file.read().splitlines()
        return data
    

    if ".tar" in path:
        return parse_tar_dir(path)
    else:
        return parse_dir(path)

if __name__ == "__main__":
    
    #get_lines_from_tar("../../out/split_fancy3.tar.gz")
    data = {}
    path =  "../../out/split_graph_baseline1"
    path = "../../out/split_fancy3.tar.gz"

    parse_path(path)
