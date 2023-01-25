from player.parser import *
from r2a.ir2a import IR2A
import time

class SARA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self,id)
        self.segment_info = []
        self.qi = []
        self.request_time = 0
        self.hn = None #media harmonica
        self.bcurr = 0 #Current buffer occupancy in seconds
        self.segment_size = 1
        self.next_qi = 0 #Bitrate of the most recently downloaded segment
        
    #requisições são movidas de cima para baixo
    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)
        
    #respostas são movidas de baixo para cima
    def handle_xml_response(self, msg):
        parsed_mpd = parse_mpd(msg.get_payload())
        t = time.perf_counter() - self.request_time
        self.segment_info.append([msg.get_bit_length(),msg.get_bit_length()/t])
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()
        self.bcurr = self.whiteboard.get_amount_video_to_play()
        bmax = self.whiteboard.get_max_buffer_size()
        beta = bmax * 0.8
        balfa = bmax * 0.4
        i = bmax * 0.15
        
        #FAST START
        if self.bcurr <= i:
            self.next_qi = 0
            print('==========FAST START============')
    
        #ADDITIVE INCREASE
        elif self.bcurr > i and self.bcurr < balfa:
            try:
                if self.qi[self.next_qi] <= self.hn:
                    self.next_qi += 1 if self.qi[self.next_qi] != self.qi[-1] else 0
                else: 
                    self.next_qi = self.choose_better_bitrate()
                print('==========ADDITIVE INCREASE============')
            except IndexError:
                pass
        #AGRESSIVE SWITCHING
        elif self.bcurr > balfa and self.bcurr <= beta:
            self.next_qi = self.choose_better_bitrate()
            print('==========AGRESSIVE SWITCHING============')

        #DELAYED DOWNLOAD
        elif self.bcurr > beta and self.bcurr <= bmax:
            self.next_qi = self.choose_better_bitrate()
            if self.bcurr > beta:
                time.sleep(1)
            pass
        print('FODASE',self.qi[self.next_qi])
        print(self.segment_info)
        msg.add_quality_id(self.qi[self.next_qi])

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        #tempo de do envio do request ate receber a resposta
        t = time.perf_counter() - self.request_time
        self.segment_size = msg.get_bit_length()
        self.segment_info.append([self.segment_size,self.segment_size/t])

        if len(self.segment_info) > 5:
            self.segment_info.pop(0)
        #realizar o calculo da média harmonica apenas quando haver no mínimo dois segmentos
        if len(self.segment_info) > 2:
            self.hn = self.calculate_harmonic_mean()

        print(f"TEMPO {self.segment_size/t}")
        print(f'TAMANHO SEGMENTO {self.segment_size}')
        print(f'MEDIA HARMONICA {self.hn}')
        #print(f'PROXIMO TAMANHO DE SEGMENTO {self.segment_size/self.hn}')
        self.send_up(msg)
    
    def calculate_harmonic_mean(self):
        #dividend = 0
        divider = 0
        for index in range(len(self.segment_info)):
            try:
                divider += 1/self.segment_info[index][0]
            except ZeroDivisionError:
                pass
        return len(self.segment_info)/divider 

    def choose_better_bitrate(self):
        if self.hn < self.qi[0]:
            return 0
        elif self.hn > self.qi[-1]:
            return 19
        else:
            for index in range(len(self.qi)):
                if self.qi[index] > self.hn:
                    return index
            return self.next_qi             
        
    def agressive_switching(self):
        pass

    def initialize(self):
        pass

    def finalization(self):
        pass
