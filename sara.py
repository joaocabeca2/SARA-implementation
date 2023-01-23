from player.parser import *
from r2a.ir2a import IR2A
import time

class SARA(IR2A):

    def __init__(self, id):
        IR2A.__init__(self,id)
        self.segment_info = []
        self.qi = []
        self.request_time = 0
        self.hn = 1 #media harmonica
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
        self.qi = parsed_mpd.get_qi()
        self.send_up(msg)
    
    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()
        self.bcurr = self.whiteboard.get_amount_video_to_play()
        bmax = 12 #self.whiteboard.get_max_buffer_size()
        beta = bmax * 0.8
        balfa = bmax * 0.4
        i = 2

        size_estimated = self.segment_size/self.hn
        #FAST START
        if self.bcurr <= i:
            self.next_qi = 0
            print('==========FAST START============')
            '''else:
                if size_estimated > self.bcurr - i:
                    self.next_qi = self.bcurr
                    print('==========FAST START2============')'''
            #ADDITIVE INCREASE
            #elif self.bcurr <= balfa:
        if  self.bcurr > i and self.bcurr < balfa:
            if self.qi[self.next_qi] != self.qi[-1]:
                self.next_qi += 1
                print('==========ADDITIVE INCREASE============')
        #AGRESSIVE SWITCHING
        elif self.bcurr > balfa and self.bcurr <= beta:
            self.agressive_switching()
            print('==========AGRESSIVE SWITCHING============')

        #DELAYED DOWNLOAD
        elif self.bcurr > beta and self.bcurr <= bmax:
            pass
        msg.add_quality_id(self.qi[self.next_qi])

        self.send_down(msg)
    
    def handle_segment_size_response(self, msg):
        #tempo de do envio do request ate receber a resposta
        t = time.perf_counter() - self.request_time
        self.segment_size = msg.get_bit_length()

        if len(self.segment_info) > 5:
            self.segment_info.pop(0)

        self.segment_info.append([self.segment_size,self.segment_size/t])

        #realizar o calculo da média harmonica apenas quando haver no mínimo dois segmentos
        if len(self.segment_info) > 2:
            self.hn = self.calculate_harmonic_mean()

        print(f"TEMPO {self.segment_size/t}")
        print(f'TAMANHO SEGMENTO {self.segment_size}')
        print(f'MEDIA HARMONICA {self.hn}')
        print(f'PROXIMO TAMANHO DE SEGMENTO {self.segment_size/self.hn}')
        self.send_up(msg)
    
    def calculate_harmonic_mean(self):
        dividend = 0
        divider = 0
        for index in range(len(self.segment_info)):
            if self.segment_info[index][1] != 0:
                dividend += self.segment_info[index][0]
                divider += self.segment_info[index][0]/self.segment_info[index][1]
        return dividend/divider           
    
    def agressive_switching(self):
        pass
    '''def fast_start(self,bitrate_estimated):
        if bitrate_estimated <= self.qi[0]:
            return self.qi[0]
        elif bitrate_estimated >= self.qi[-1]:
            return self.qi[-1]
        else:
            for index in range(len(self.qi[self.next_qi:])):'''


    def initialize(self):
        pass

    def finalization(self):
        pass
