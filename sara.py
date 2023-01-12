from player.parser import *
from r2a.ir2a import IR2A
import time

class SARA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self,id)
        self.throughputs = []
        self.qi = []
        self.request_time = 0
        self.response_time = 0
        self.parsed_mpd = None
        self.bcurr = 0 # ocupaçao do buffer
        
    #requisições são movidas de cima para baixo
    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)
        
    #respostas são movidas de baixo para cima
    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()
        self.response_time = time.perf_counter()

        #tempo de do envio do request ate receber a resposta
        t = self.response_time - self.request_time

        #adicionando as taxas de transferencia na lista
        self.throughputs.append(msg.get_bit_length()/t)

        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):
        selected_qi = 0
        self.request_time = time.perf_counter()
        self.bcurr = self.whiteboard.get_amount_video_to_play()
        
        #FAST START –  Bcurr <= I
        if self.bcurr <= msg.get_bit_length():
            #print(f"Menor taxa de bits = {min(self.throughputs)}")
            selected_qi = min(self.qi)
        
        msg.add_quality_id(self.qi[0])

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        self.response_time = time.perf_counter()

        #tempo de do envio do request ate receber a resposta
        t = self.response_time - self.request_time
        #print('>>>>>>>>>>>>>>>',msg.get_bit_length())

        self.send_up(msg)
    
    def initialize(self):
        pass

    def finalization(self):
        pass
