import re

def match_new_headers(data,already_found_headers):
	"""
		Returns <list>new_headers, <dict>mapped_data
	"""
	first_pattern = "\s?(?!Submit|Explorer|Redirect|Page|True|False|Idle Process)(?<![\:\=]\s)(Size in bytes|(?:X(?:-[A-Z]{2})?)?(?:[^\w]\w+\s?[\-\_]\s?)?(?:(?<![a-z])(?:(?:[A-Z][a-z]{1,}|(?<![\w])[A-Z]{2})(?:\s?[\-\_]\s?[A-Z][a-z]{1,}){0,}|Size in|HTTPS?|DLL|DNS|I[DP]|(?:MD|SHA)\d{1,4}(?:Sum)?|PID)(?![A-Z])\s?|URL){1,3}):\s"
	second_pattern = "\s{}".format(first_pattern[3:])
	pattern = re.compile(first_pattern)

	new_headers = []
	data_copy = data
	previous_header = None
	matched_data = {}
	change_pattern = True
	while True:
		try:
			# check already known headers before resorting to a horrible regex
			for position, header in already_found_headers.items():
				header = "{}:".format(header)
				if header in data:
					# check there's not another potential header prior to this one
					if data.index(header)+len(header) == data.index(":")+1:
						# check "Parent" shouldn't come before it
						if "Parent" in data[:data.index(header)]:
							header = "Parent {}".format(header)
						match = header[:-1]
						full_match = header
						break
			else:
				# match the header
				match = pattern.search(data)
				full_match = match.group()
				match = match.group(1)
			# Hacky fix for "System Idle Process Process Name:"
			if " " in match:
				if match.split(" ")[0] in match.split(" ")[1:]:
					match = " ".join(match.split(" ")[1:])
			if '"' in match[0] or " " in match[0]:
				match = match[1:]
			# strip the header out 
			next_data = data.split(full_match,1)[1]
			prev_data = data.split(full_match,1)[0]
			# format like original headers
			header = '{}'.format(match)
			# prev_data has data to append to the previous header
			matched_data[previous_header] = '{}'.format(prev_data.strip().replace("\n","").replace('"','\\"'))
			new_headers.append(header)

			data = next_data
			previous_header = header
			if change_pattern:
				pattern  = re.compile(second_pattern)
				change_pattern = False
		except AttributeError:
			break
	# add last data
	if data[-2] == '"':
		matched_data[previous_header] = '{}'.format(data[:-2].strip())
	else:
		matched_data[previous_header] = '{}'.format(data.strip())
	return new_headers, matched_data

def match_content_to_known_headers(known_headers, lines):
	"""
		returns dict{ position : header }, dict{ line_number : dict{ headers: data } }
	"""
	print("Parsing the data and mapping new headers...")

	# instantiate each header with a number to position it in the new csv file
	headers = {}
	for i in range(len(known_headers)-1):
		headers[i+1] = known_headers[i]

	dict_of_lines = {}
	line_as_dict = {}
	# initialise known headers into line_as_dict
	for position, header in headers.items():
		line_as_dict[header] = '"{}"'

	# loop through lines
	line_number = 0
	line_finished = True
	for line in lines:
		if len(line) < 2: continue
		if line_finished:
			line_as_dict_copy = line_as_dict

			# split by known headers and minus the summary field
			original = line
			line = line.split(",",len(known_headers)-1)
			
			# format the simple stuff and add to the line_as_dict_copy
			for position in range(1, len(line)):
				line_as_dict_copy[headers[position]] = '{}'.format(line[position-1].replace('"','\"')) 
				# -1 because the line split starts from 0 but headers are mapped 1+

			# pull out new headers and match the content for the Summary field
			summary_field = line[-1]
			if summary_field[0] == '"' and not summary_field[-2] == '"': 
				line_finished = False
			else:
				line_number += 1
			new_headers, mapped_data = match_new_headers(summary_field,headers)
		else:
			if line[-2] == '"': 
				line_finished = True
				line_number += 1
			new_headers, mapped_data = match_new_headers(line,headers)
		# both cases finish at the same point

		# add the new headers with an incremented position
		for header in new_headers:
			if header in headers.values(): continue
			print('New header: {}'.format(header))
			headers[len(headers)+1] = header

		# add the mapped_data to the line_as_dict_copy
		line_as_dict_copy = {**line_as_dict_copy, **mapped_data}

		if line_finished:
			dict_of_lines[line_number] = line_as_dict_copy
	return headers, dict_of_lines

def read_file(infile):
	"""
		Returns <dict>headers, <list>lines
	"""
	try:
		with open(infile, "r", encoding="utf-8") as f:
			lines = f.readlines()
			# formats original headers without the "Summary" header.
			header_line = lines[0]
			# stop collision with similarily named fields such as (http) Host
			original_headers = ['Original {}'.format(s.strip()) for s in header_line.split(",")]
			lines = lines[1:]
		return original_headers, lines
	except IOError:
		print("[!] {} caused an exception. Check that the file exists and contains the headers: Host,Agent ID,ItemType,Summary".format(infile))
		exit(1)

def csv_map_line_to_headers(headers, line_dict):
	"""
		Maps the line fields to headers in the correct order
	"""
	inverse_headers = dict((v,k) for k,v in headers.items())
	new_line = ""
	for position, header in headers.items():
		if header in line_dict.keys():
			new_line += '"{}",'.format(line_dict.get(header))
		else:
			new_line += '"",'
	if new_line[-1] == ",":
		new_line = new_line[:-1]
	return new_line

def write_out_content(headers, data, filename, output_type):
	"""
		writes the file to supported filetypes
	"""
	with open(filename,"w", encoding="utf-8") as f:
		if output_type == "csv":
			# join headers
			header_line = ','.join([ '"{}"'.format(headers.get(i)) for i in range(1,len(headers)+1)])
			f.write(header_line+"\n")

			# write the data out
			for line_number in range(1,len(data)+1):
				line_dict = data[line_number]
				# 1, {'"Username"':'"lobs"'}
				# need to work out header mapping
				line = csv_map_line_to_headers(headers, line_dict)
				f.write(line+"\n")
		elif output_type == "json":
			import json
			json_data = { "data" : [] }
			for line_number in range(1,len(data)+1):
				json_data["data"].append(data[line_number])
			json.dump(json_data,f,indent=4)
		elif output_type == "json_splunk":
			import json
			for line_number in range(1,len(data)+1):
				json.dump(data[line_number],f,indent=4)
		else:
			raise TypeError("Unsupported filetype '{}'".format(output_type))
	print("Written file: {}".format(filename))


def main(infile, outfile, output_type):
	original_headers, lines = read_file(infile)
	headers, data = match_content_to_known_headers(original_headers, lines)
	write_out_content(headers, data, outfile, output_type)

if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument("-f","--filename",
		action="store",
		required=True,
		help='''
		Provide a filename to parse.
		''')
	parser.add_argument("-w","--write-file",
		action="store",
		help='''
		Provide a filename to write the new file out to. If none specified, the script will write it out to a file with "new_" prepended to the input file.
		''')
	
	file_type_group = parser.add_mutually_exclusive_group(required=False)
	file_type_group.add_argument("--csv",
		action="store_true",
		help='''
		[default option] Write the data out as CSV.
		''')
	file_type_group.add_argument("--json-splunk",
		action="store_true",
		help='''
		Write the data out as JSON for Splunk.
		''')
	file_type_group.add_argument("--json",
		action="store_true",
		help='''
		Write the data out as ordinary JSON.
		''')


	args = parser.parse_args()
	filename = args.filename
	if filename[0:2] == ".\\": filename = filename[2:]

	output_type = "csv"
	if args.json:
		output_type = "json"
		output_filename = "new_{}".format(filename.replace(".csv",".json"))
	elif args.json_splunk:
		output_type = "json_splunk"
		output_filename = "new_{}".format(filename.replace(".csv",".json"))
	else:
		output_filename = "new_{}".format(filename)
	if args.write_file:
		output_filename = args.write_file

	main(filename, output_filename, output_type=output_type)
		