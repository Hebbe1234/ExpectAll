def ReadFile(path):
	file = open(path,"r") #Opens file
	data = file.read() #Save file data in string
	data = data.splitlines() #Split lines so you have List of all lines in file
	file.close() #Close file
	return data #Return list with file's rows

x = ReadFile("../../out/wavelengths_static_demands.csv")
print(x)