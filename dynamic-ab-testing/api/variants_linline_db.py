from datetime import datetime

class VariantsInlineDB:
    '''
    실행 방법:

    from api.variants_linline_db import VariantsInlineDB 

    vdb = VariantsInlineDB()

    variant_record = vdb.add_variant(variant_name="Challenger", 
                                invocation=0, 
                                conversion=0, 
                                reward=0, 
                                initial_variant_weight=1, 
                                verbose=False)

    variant_record = vdb.add_variant(variant_name="Champion", 
                                invocation=0, 
                                conversion=0, 
                                reward=0, 
                                initial_variant_weight=1, 
                                verbose=False)

    print(json.dumps(vdb.variant_dic, indent=2))    
    
    variant_name = "Champion"
    variant_record = vdb.update_variant(variant_name = variant_name, 
                                        invocation=1, 
                                        conversion=1, 
                                        reward=1, 
                                        verbose=True
                                        )

    # print(json.dumps(vdb.variant_dic, indent=2))

    variant_name = "Challenger"
    variant_record = vdb.update_variant(variant_name = variant_name, 
                                        invocation=1, 
                                        conversion=1, 
                                        reward=1, 
                                        verbose=False
                                        )

    print(json.dumps(vdb.variant_dic, indent=2))

    vdb.reset()
    print(json.dumps(vdb.variant_dic, indent=2))    
    '''
    def __init__(self):
        self.variant_dic = {}    
        
    def reset(self):
        self.variant_dic = {}            
            
    def get_variant(self, variant_name):
        '''
        user_no 를 입력하면 최근 레코드를 제공
        get_userno(user_dic, user_no='meta' )
        '''
        variant_data = self.variant_dic.get(variant_name)
        return variant_data

    def insert_variant(self, variant_name, variant_data, verbose=False): # 유저 사전에 입력     
    #def insert_userno(user_dic, user_no, user_data, verbose=False):
        '''
        user_no 가 없으면 유저 사전에 입력 함.
        user_no 가 있으면 기존 것을 제거하고, 새로이 레코드 생성하여 입력
        # user_data = {'timestamp': '2021-05-15 20:10:10','recent_duration': 350,'recent_freq': 100, 'threshold': 600}
        # insert_userno(user_dic, user_no='user_1', user_data = user_data)
        '''

        if self.variant_dic.get(variant_name) == None:        
            self.variant_dic[variant_name] = variant_data
            output = self.variant_dic.get(variant_name)    
            if verbose:
                print(f'{output} is inserted')
        else:
            self.variant_dic.pop(variant_name)
            self.variant_dic[variant_name] = variant_data        
            if verbose:
                print("userno info is updated")
                print(self.variant_dic.get(variant_name))



    def add_variant(self, variant_name, invocation, conversion, reward, initial_variant_weight, verbose=False):
        '''
        유저가 없기에 새로운 유저를 유저 사전에 입력 함.
        '''
        regdate = f"{datetime.now():%Y-%m-%d-%H-%M-%S}"            
        #recent_duration = 9999999 # 처음 트랜잭션은 큰 값으로 지정
        recent_duration = 0 # 처음 트랜잭션은 0 으로 지정            
        recent_freq = 1 # 처음 트랜잭션이기에 1 으로 설정
        variant_data  = {
                         'timestamp': regdate, 
                         'invocation': invocation,
                         'conversion': conversion, 
                         'reward': reward,                      
                         'initial_variant_weight': initial_variant_weight, 
                         } # 유저 사전에 담을 레코드

        if verbose:
            print("add_variant()")
            print("variant_name: ", variant_name)
            print("invocation: ", invocation)        
            print("conversion: \n", conversion)        
            print("reward: \n", reward)                


        self.insert_variant(variant_name= variant_name, variant_data = variant_data) # 유저 사전에 입력     
        if verbose:
            print("added_variant_dic: \n", added_variant_dic )

        return variant_data



    def update_variant(self, variant_name, invocation, conversion, reward, verbose=False ):
        '''
        유저의 레코드를 업데이트를 함.
        '''
        regdate = f"{datetime.now():%Y-%m-%d-%H-%M-%S}"   
        
        variant_data = self.get_variant(variant_name)
        # print("variant_data: ", variant_data)
        
        new_invocation = int(variant_data['invocation'] + invocation) # 현재 트랜잭션을 더함.    
        new_conversion = int(variant_data['conversion'] + conversion) # 현재 트랜잭션을 더함.        
        new_reward = int(variant_data['reward'] + reward) # 현재 트랜잭션을 더함.            
        initial_variant_weight = variant_data['initial_variant_weight'] 

        variant_data  = {
                         'timestamp': regdate, 
                         'invocation': new_invocation,
                         'conversion': new_conversion, 
                         'reward': new_reward,                      
                         'initial_variant_weight': initial_variant_weight, 
                         } # 유저 사전에 담을 레코드

 

        self.insert_variant(variant_name= variant_name, variant_data = variant_data)                


        if verbose:
            print("variant_name: ", variant_name)            
            print("new_invocation: ", new_invocation)            
            print("new_conversion: ", new_conversion)                
            print("new_reward: ", new_reward)
            print("variant_data: \n", variant_data)            

        return variant_data
    
    def get_variant_metrics(self):
        challenger_variant_data = self.get_variant(variant_name = 'Challenger')
        challenger_invocaton_conut = challenger_variant_data['invocation']
        challenger_reward_sum = challenger_variant_data['reward']

        champion_variant_data = self.get_variant(variant_name = 'Champion')
        champion_invocaton_conut = champion_variant_data['invocation']
        champion_reward_sum = champion_variant_data['reward']

        variant_metrics_list = [
            {
                "variant_name": f"Champion",
                "invocation_count": int(f"{champion_invocaton_conut}"),
                "reward_sum": int(f"{champion_reward_sum}"),
            },
            {
                "variant_name": "Challenger",
                "invocation_count": int(f"{challenger_invocaton_conut}"),
                "reward_sum": int(f"{challenger_reward_sum}"),

            }
        ]
        
        return variant_metrics_list
        
    

        


            