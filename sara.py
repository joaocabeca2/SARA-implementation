from player.parser import *
from r2a.ir2a import IR2A
import time

class SARA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self,id)
        #self.throughputs = []
        self.qi = []
        self.segments_size = []
        self.request_time = 0
        self.hn = 1 #media harmonica
        self.bcurr = 0 #Current buffer occupancy in seconds
        self.weight = None
        self.segment_size = 1
        self.index_segment = None #Segment number of the most recent download
        self.current_qi = 0 #Bitrate of the most recently downloaded segment
        
    #requisições são movidas de cima para baixo
    def handle_xml_request(self, msg):
        self.send_down(msg)
        
    #respostas são movidas de baixo para cima
    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):
        self.bcurr = self.whiteboard.get_amount_video_to_play()
        bmax = self.whiteboard.get_max_buffer_size()
        beta = bmax * 0.8
        balfa = bmax * 0.4
        i = bmax * 0.15

        self.request_time = time.perf_counter()

        size_estimated = self.segment_size/self.hn
        #FAST START
        if self.bcurr <= i:
            self.current_qi = 0
            print('==========FAST START============')
        else:
            if size_estimated > self.bcurr - i:
                self.fast_start(size_estimated)
                print('==========FAST START2============')
            #ADDITIVE INCREASE
            elif self.bcurr <= balfa:
                if size_estimated < self.bcurr - i:
                    if self.qi[self.current_qi] != self.qi[-1]:
                        self.current_qi += 1
                        print('==========ADDITIVE INCREASE============')
            #AGRESSIVE SWITCHING
            elif self.bcurr > balfa and self.bcurr <= beta:
                self.agressive_switching()
                print('==========AGRESSIVE SWITCHING============')

            #DELAYED DOWNLOAD
            elif self.bcurr > beta and self.bcurr <= bmax:
                pass
        msg.add_quality_id(self.qi[self.current_qi])

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        #tempo de do envio do request ate receber a resposta
        t = time.perf_counter() - self.request_time
        self.segment_size = msg.get_bit_length()
        self.weight = self.segment_size/1000

        #self.throughputs.append(self.segment_size/t)
        self.segments_size.append(self.segment_size) 
        self.hn = self.calculate_harmonic_mean(t)

        self.send_up(msg)
    
    def calculate_harmonic_mean(self,t):
        dividend = 0
        divider = 0
        for segment in self.segments_size:
            if segment != 0:
                weight = segment/1000
                dividend += weight
                divider += (weight)/(segment/t)
        return dividend/divider
    
    def agressive_switching(self):
        rate = 0
        for index in range(len(self.qi[self.current_qi:])):
            if self.qi[index] >= self.hn:
                x = self.hn - self.qi[index]
                if x <= rate:
                    rate = x
                    self.current_qi = index

    def fast_start(self,size_estimated):
        rate = 0
        for index in range(len(self.qi)):
            if self.qi[index] <= size_estimated:
                x = size_estimated - self.qi[index]
                if x <= rate:
                    rate = x
                    self.current_qi = index

    def initialize(self):
        pass

    def finalization(self):
        pass
