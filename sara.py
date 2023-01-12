from player.parser import *
from r2a.ir2a import IR2A
import time

class SARA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self,id)
        self.throughputs = []
        self.qi = []
        self.segments_size = []
        self.request_time = 0
        self.hn = 1 #media harmonica
        self.bcurr = 0 # ocupaçao do buffer
        self.bmax = self.whiteboard.get_max_buffer_size()
        
    #requisições são movidas de cima para baixo
    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)
        
    #respostas são movidas de baixo para cima
    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()

        #tempo de do envio do request ate receber a resposta
        t = time.perf_counter() - self.request_time

        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):
        selected_qi = self.qi[0]
        self.bcurr = self.whiteboard.get_amount_video_to_play()
        beta = self.bmax * 0.8
        balfa = self.bmax * 0.4
        i = self.bmax * 0.15

        self.request_time = time.perf_counter()

        #FAST START
        if self.bcurr <= i:
            selected_id = min(self.qi)
        else:
            pass
        
        msg.add_quality_id(selected_id)

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        #tempo de do envio do request ate receber a resposta
        t = time.perf_counter() - self.request_time
        segment_size = msg.get_bit_length()

        print('BUFFER SIZE',self.bcurr)
        print('MAXIMO BUFFER',self.bmax)
        print('MEDIA HARMONICA',self.hn)

        self.throughputs.append(segment_size/t)
        self.segments_size.append(segment_size) 
        self.hn += self.calculate_harmonic_mean(t,segment_size)

        self.send_up(msg)
    
    def calculate_harmonic_mean(self,t,segment_size):
        wi = segment_size*len(self.segments_size)+1
        di = segment_size*(len(self.segments_size)/t)
        return wi/di

    def initialize(self):
        pass

    def finalization(self):
        pass
