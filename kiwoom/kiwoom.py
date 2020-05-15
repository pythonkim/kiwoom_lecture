from PyQt5.QAxContainer import * #QAxWidget을 가져오기 위해 import
from PyQt5.QtCore import * #QEventLoop를 쓰기 위해 import
from config.errCode import * #만들어 놓은 에러코드를 쓰기 위해 import

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__() # 위에 상속받은 초기값을 쓸려면 이렇게 해야 한다
        print("Kiwoom 클래스 입니다")
        #####################eventloop 모음
        self.login_event_loop = None
        self.detail_account_info_event_loop = QEventLoop()
        ####################################

        ########################스크린번호 모음
        self.screen_my_info = "2000"


        ################변수모음
        self.account_num = None
        self.account_stock_dict = {} #계좌평가잔고 보유종목을 담을 dict
        self.not_account_stock_dict = {} #미체결잔고의 보유종목을 담을 dict
        #######################################
        #############계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5


        self.get_ocx_instance() # OCX 방식을 파이썬에 사용할 수 있게 반환해 주는 함수 실행
        self.event_slots() # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.signal_login_commConnect() #로그인 하는거
        self.get_account_info() #계좌가져오는거
        self.detail_account_info() #예수금 가져오는것!
        self.detail_account_mystock() #계좌평가 잔고내역 가져오는것
        self.not_concluded_account()#미체결 내역 가져오는것
        print(dir(self))


    def get_ocx_instance(self): #키움증권과 연결하는것!
        self.setControl("KHOPENAPI.KHOpenAPICTrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) #
        self.OnReceiveTrData.connect(self.trdata_slot)


    def login_slot(self, errCode):
        #print(errCode)
        print(errors(errCode))

        self.login_event_loop.exit()

    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()")

        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def get_account_info(self):
        account_list = self.dynamicCall("GetLogininfo(String)","ACCNO")
        self.account_num = account_list.split(';')[0]
        print("나의 보유 계좌번호 %s" % self.account_num) #8135257911
        account_list = self.dynamicCall("GetLogininfo(String)", "USER_ID")
        print(account_list)

    def detail_account_info(self):
        print("예수금을 요청하는 부분")

        self.dynamicCall('SetInputValue(String,String','계좌번호',self.account_num)
        self.dynamicCall('SetInputValue(String,String', '비밀번호', 0000)
        self.dynamicCall('SetInputValue(String,String', '비밀번호입력매체구분', 00)
        self.dynamicCall('SetInputValue(String,String', '조회구분', 2)
        self.dynamicCall('CommRqData(String,String,int,String)',"예수금상세현황요청","opw00001",'0',self.screen_my_info)

        self.detail_account_info_event_loop = QEventLoop()
        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self,sPrevNext="0"):
        print("계좌평가 잔고내역 요청 연속조회 %s" % sPrevNext)
        self.dynamicCall('SetInputValue(String,String','계좌번호',self.account_num)
        self.dynamicCall('SetInputValue(String,String', '비밀번호', 0000)
        self.dynamicCall('SetInputValue(String,String', '비밀번호입력매체구분', 00)
        self.dynamicCall('SetInputValue(String,String', '조회구분', 2)
        self.dynamicCall('CommRqData(String,String,int,String)', "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)


        self.detail_account_info_event_loop.exec_()

    def not_concluded_account(self, sPrevNext="0"):
        print("미 체결 내역 조회")
        self.dynamicCall('SetInputValue(QString,QString','계좌번호',self.account_num)
        self.dynamicCall('SetInputValue(QString,QString', '체결구분', '1')
        self.dynamicCall('SetInputValue(QString,QString', '매매구분', '0')
        self.dynamicCall('CommRqData(String,String,int,String)', "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def trdata_slot(self,sScrNo,sRQName,sTrCode,sRecordName,sPrevNext):
        '''
        tr요청을 받는 구역이다! 슬롯이다
        :param sScrNo: 스크린번호
        :param sRQName: 내가 요청했을 때 지은 이름
        :param sTrCode: 요청id, tr코드
        :param sRecordName: 사용 안함
        :param sPrevNext: 다음 페이지가 있는지
        :return:
        '''

        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode,sRQName,0,"예수금")
            print("예수금 %s " % int(deposit))

            self.use_money = int(deposit) * self.use_money_percent #예수금을 50%만
            self.use_money = self.use_money / 4 #그걸 또 4분에 1



            ok_deposit = self.dynamicCall("GetCommData(String,String,int,String)", sTrCode, sRQName, 0, "출금가능금액")
            print("출금가능금액 %s" % int(ok_deposit))

            self.detail_account_info_event_loop.exit()



        if sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode,sRQName,0,"총매입금액")
            total_buy_money_result = int(total_buy_money)
            print("총매입금액 %s" % total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode,sRQName,0,"총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            print("총 수익률(%%) : %s" % total_profit_loss_rate_result)



            total_profit_loss_money = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode,sRQName,0,"총평가손익금액")
            total_profit_loss_money_result = int(total_profit_loss_money)
            print("총평가손익금액 : %s" %total_profit_loss_money_result)


            rows = self.dynamicCall("GetRepeatCnt(QString, QString)",sTrCode, sRQName) #멀티데이터의 정보를 가져오겠다는뜻(GetRepeatCnt
            #또한 20개씩 밖에 못가져온다
            cnt = 0
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"종목번호")
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"종목명")
                stock_quantity = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"보유수량")
                buy_price = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"매입가")
                learn_rate = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"현재가")
                total_chegual_price = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"매매가능수량")

                if code in self.account_stock_dict:
                    pass
                else:
                    self.account_stock_dict.update({code:{}})

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())

                self.account_stock_dict[code].update({"종목명":code_nm})
                self.account_stock_dict[code].update({"보유수량": stock_quantity})
                self.account_stock_dict[code].update({"매입가": buy_price})
                self.account_stock_dict[code].update({"수익률(%)": learn_rate})
                self.account_stock_dict[code].update({"현재가": current_price})
                self.account_stock_dict[code].update({"매입금액": total_chegual_price})
                self.account_stock_dict[code].update({"매매가능수량": possible_quantity})

                cnt += 1
            print("계좌에 가지고 있는 종목 %s" % self.account_stock_dict)
            print("계좌에 가지고 있는 종목 수 %s" % cnt)


            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2") #보유종목이 20개가 넘으면 2가 된다.
            else:
                self.detail_account_info_event_loop.exit()

        elif sRQName == "실시간미체결요청":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)",sTrCode, sRQName) #멀티데이터의 정보를 가져오겠다는뜻(GetRepeatCnt
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"종목코드")
                code_nm = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"종목명")
                order_no = self.dynamicCall("GetCommData(QString,QString,int,QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"주문수량")
                order_price = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"주문구분")
                not_quantity = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString,QString,int,QString)",sTrCode,sRQName,i,"체결량")

                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if order_no in self.not_account_stock_dict:
                    pass
                else:
                    self.not_account_stock_dict[order_no] = {}

                self.not_account_stock_dict[order_no].update({"종목코드": code})
                self.not_account_stock_dict[order_no].update({"종목명": code_nm})
                self.not_account_stock_dict[order_no].update({"주문번호": order_no})
                self.not_account_stock_dict[order_no].update({"주문상태": order_status})
                self.not_account_stock_dict[order_no].update({"주문수량": order_quantity})
                self.not_account_stock_dict[order_no].update({"주문가격": order_price})
                self.not_account_stock_dict[order_no].update({"주문구분": order_gubun})
                self.not_account_stock_dict[order_no].update({"미체결수량": not_quantity})
                self.not_account_stock_dict[order_no].update({"체결량": ok_quantity})

                print("미체결 종목 : %s" % self.not_account_stock_dict[order_no])
                print("아흥")
            self.detail_account_info_event_loop.exit()












