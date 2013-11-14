#!/usr/bin/python

import string
import math
import binascii
import hashlib
import os
import errno
import imghdr
import time

BUFFER_SIZE = 10485760.0 # Bytes (10MB)
MAX_FILE_SIZE = 1048576.0 # Bytes (1MB)
PATH = '/Users/andrewvojak/Desktop/test_disk_images/larryFlashDrive.dd'

SOI = 'ffd8'
SOS = 'ffda'
EOI = 'ffd9'
JFIF = '4a46494600'

def main():

	images_found = 0

	soi_indices = []
	sos_indices = []
	eoi_indices = []

	# Get image size
	disk_size = os.path.getsize(PATH)

	# Determine the number of chunks
	num_chunks = int(math.ceil(disk_size / BUFFER_SIZE))

	print("Loading {0} ({1}B)".format(PATH, disk_size))
	print("Maximum JPEG file size set to {0}B".format(MAX_FILE_SIZE))
	print("Using {0} buffers of size {1}B".format(num_chunks, BUFFER_SIZE))
	print("---- First Pass ----")

	curr_chunk = 0
	f_in = open(PATH, 'rb')
	while True:
		content = f_in.read(int(BUFFER_SIZE))
		if content:
			print("Examining chunk {0}/{1}".format(curr_chunk + 1, num_chunks))
			# Convert to hex
			hex_content = binascii.hexlify(content)

			# Find SOI markers
			index = hex_content.find(SOI, 0)
			while index != -1:
				if (index + 22) < len(hex_content):
					header = hex_content[index : index + 22]
					if header.find(JFIF) != -1:
						soi_indices.append(curr_chunk * BUFFER_SIZE * 2 + index)
						#print(hex_content[index : index + 22])
				index = hex_content.find(SOI, index + 4)

			# Find SOS markers
			index = hex_content.find(SOS, 0)
			while index != -1:
				#print("\tFound SOS marker")
				sos_indices.append(curr_chunk * BUFFER_SIZE * 2 + index)
				index = hex_content.find(SOS, index + 4)

			# Find EOI markers
			index = hex_content.find(EOI, 0)
			while index != -1:
				#print("\tFound EOI marker")
				eoi_indices.append(curr_chunk * BUFFER_SIZE * 2 + index)
				index = hex_content.find(EOI, index + 4)

			curr_chunk += 1
		else:
			break


	# Find potential SOI and EOI pairings
	pairs = []
	count = 0
	for soi_i in range(0, len(soi_indices)):
		for eoi_i in range(0, len(eoi_indices)):
			if (eoi_indices[eoi_i] > soi_indices[soi_i]) and ((eoi_indices[eoi_i] - soi_indices[soi_i]) / 2 <= MAX_FILE_SIZE):
				for sos_i in range(0, len(sos_indices)):
					if sos_indices[sos_i] > soi_indices[soi_i] and sos_indices[sos_i] < eoi_indices[eoi_i]:
						pairs.append((soi_indices[soi_i], eoi_indices[eoi_i] + 4))
						break

	# Second pass
	print("---- Second Pass ----")

	curr_chunk = 0
	curr_pair = 0
	f_in = open(PATH, 'rb')
	while True:
		content = f_in.read(int(BUFFER_SIZE))
		if content:
			print("Examining chunk {0}/{1}".format(curr_chunk + 1, num_chunks))
			# Convert to hex
			hex_content = binascii.hexlify(content)

			while (curr_pair < len(pairs)) and (pairs[curr_pair][0] - (curr_chunk * BUFFER_SIZE * 2)) < BUFFER_SIZE * 2:
				print("Handling pair {0}/{1}".format(curr_pair + 1, len(pairs)))

				# Check if pair spans the buffer
				if pairs[curr_pair][1] > ((curr_chunk + 1) * BUFFER_SIZE * 2):
					print("Image spans buffer")
				# Otherwise, business as usual
				else:
					lb = int(pairs[curr_pair][0] - (curr_chunk * BUFFER_SIZE * 2))
					ub = int(pairs[curr_pair][1] - (curr_chunk * BUFFER_SIZE * 2))
					img = hex_content[lb : ub]
					if try_image(img) == True:
						images_found += 1

				curr_pair += 1

			curr_chunk += 1
		else:
			break

	return images_found

# Attempt to write the image
def try_image(hex_content):

	filename = None
	try:
		bytes = binascii.unhexlify(hex_content)
		filename = '/Users/andrewvojak/Desktop/output/' + hashlib.md5(bytes).hexdigest() + '.jpg'
		f_out = open(filename, 'wb')
		f_out.write(bytes)
		f_out.close()
	except:
		print("Invalid [binascii]")
		return

	if imghdr.what(filename) == None:
		os.remove(filename)
		print("Invalid [imghdr]")
	else:
		print("**** Image Saved ****")
		return True

def hex_to_int(h):
	return int(h, 16)

if __name__ == '__main__':
	print("\n--------------------------------------")
	print("File Carver preset with following settings:")
	print("Disk image location: {0}".format(PATH))
	print("Maximum file size: {0}".format(MAX_FILE_SIZE))
	print("Buffer size: {0}".format(BUFFER_SIZE))
	print("\n--------------------------------------")
	s = time.clock()
	images_found = main()
	print("Found {0} JPEG images in {1:.4f} seconds".format(images_found, time.clock() - s))