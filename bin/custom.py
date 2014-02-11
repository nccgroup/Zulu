#######################################################################################################################################
# Zulu custom script file - when ZuluScript is enabled, this script will be executed prior to each packet being sent 
#			    (including unmodified packets), but after any fuzz data has been applied to the packet
#
# Variables that can be referenced:
#
# self.packets_selected_to_send = list of packets selected to send [[packet number, data],[packet number, data]...]
#
# self.all_packets_captured = list of all packets captured [[[source IP,source port],data], [[source IP,source port],data]...]
#
# self.modified_data = list of all the data in the current packet (after any modification with fuzzpoint data) [byte1, byte2, byte3...] 
#
# self.current_packet_number = the number of the current packet being processed (packet 0 is the first packet)
#
# Below are two example functions:
#
# test() just proves that ZuluScript is functioning correctly and demonstrates the data that can be accessed
# UpdateContentLengthField() is an example script to update a Content Length field within an HTTP packet 
#
#######################################################################################################################################

class ZuluScript:
    """
    Zulu custom scripting interface
    """
   
    def	__init__(self,zulu):
	print "---ZuluScript started---"	
	self.zulu = zulu

	#self.test()

	self.UpdateContentLengthField(0)

	print "---ZuluScript complete---"
	return



    def test(self):
	print "-----------------------------"
	print "ZuluScript test:"
	print
	print "self.packets_selected_to_send"
	print
	print self.zulu.packets_selected_to_send
	print
	print "self.all_packets_captured"
	print
	print self.zulu.all_packets_captured
	print	
	print "self.modified_data"
	print
	print self.zulu.modified_data
	print
	print "self.current_packet_number"
	print
	print self.zulu.current_packet_number
	print
	print "-----------------------------"	
	return




    def	UpdateContentLengthField(self, packet_num):
    
    	# UpdateContentLengthField() - Updates an HTTP Content length field within a packet after fuzz data has been inserted

    	# packet_num - the number of the packet containing the length field

	if self.zulu.current_packet_number != packet_num:
		return
   
	length = 0
	lengthtext = ""
	length_lst = []
	data = ""
	temp_data = ""
	field_pos = 0

	x = 0
	while x < len(self.zulu.modified_data):
		data += self.zulu.modified_data[x]
		x+=1

	
	field_pos = data.find("Content-Length")
	if field_pos == -1:
		print "No Content-Length header"
		return

	field_pos += 15

	start = data.find("\r\n\r\n")
	if start == -1:
		print "No POST data"
		return

	start += 4

	end = len(self.zulu.modified_data)-1

	length = end - start
	lengthtext = "%d" % length

	x = 0
	while x < field_pos:
		temp_data += self.zulu.modified_data[x]
		x+=1

	temp_data += " "
	temp_data += lengthtext
	temp_data += "\x0a"

	while self.zulu.modified_data[x] != "\x0a":
		x+=1	

	x+=1

	while x < end:

		temp_data += self.zulu.modified_data[x]
		x+=1

	x=0
	self.zulu.modified_data = []
	while x < len(temp_data):
		self.zulu.modified_data.append(temp_data[x])
		x+=1






