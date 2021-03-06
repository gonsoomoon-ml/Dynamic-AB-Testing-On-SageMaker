from IPython.display import display as dp

import boto3
import json
import pandas as pd

import pandas as pd
import sys
sys.path.append('./api')
from api.test_algorithm import test_thompson_sampling_w_variants

runtime = boto3.Session().client('sagemaker-runtime')

#########################################

def chunker(seq, batch_size):
    return (seq[pos:pos + batch_size] for pos in range(0, len(seq), batch_size))

def parse_predictions(results):
    return [(result['label'][0] == '__label__Helpful', result['prob'][0]) for result in results]    

def predict(endpoint_name, variant_name, data, batch_size=50):
    '''
    boto3 API, "invoke_endpoint", 를 호출하여 예측 결과를 얻은 후에 레이블 TRUE/FALSE 및 confidense score 를 제공 
    '''
    all_predictions = []
    for array in chunker(data, batch_size):
        payload = {"instances" : array, "configuration": {"k": 1} }
        try:
            response = runtime.invoke_endpoint(
                EndpointName = endpoint_name, 
                TargetVariant = variant_name,
                ContentType = 'application/json',                        
                Body = json.dumps(payload))
            predictions = json.loads(response['Body'].read())            
            all_predictions += parse_predictions(predictions)
        except Exception as e:
            print(e)
            print(payload)
    return all_predictions

#########################################

def predict_with_db(endpoint_name, variant_name, data, batch_size, variant_db):
    '''
    predict() 역할은 동일하며, variant_db 에 invocation 한번을 추가 함.
    '''
    all_predictions = []
    for array in chunker(data, batch_size):
        payload = {"instances" : array, "configuration": {"k": 1} }
        try:
            response = runtime.invoke_endpoint(
                EndpointName = endpoint_name, 
                TargetVariant = variant_name,
                ContentType = 'application/json',                        
                Body = json.dumps(payload))
            predictions = json.loads(response['Body'].read())            
            all_predictions += parse_predictions(predictions)
            ## variant_db에 업데이트
            variant_record = variant_db.update_variant(variant_name = variant_name, 
                                                invocation=1, 
                                                conversion=0, 
                                                reward=0, 
                                                verbose=False
                                                )

            
        except Exception as e:
            print(e)
            print(payload)
    return all_predictions

#########################################

def join_test(test_df, predictions, variant_name):
    '''
    test 데이터, 추론 데이터를 머지 함.
    '''
    pred_df = pd.DataFrame(predictions, columns=['is_helpful_prediction', 'is_helpful_prob'])
    pred_df['variant_name'] = variant_name
    return test_df[['is_helpful']].join(pred_df)

def get_target_variant(variant_db):
    '''
    variant_db 에서 variant_metrics (variant 별로 invocations, rewards 숫자) 를 가져온 후에 test_thompson_sampling_w_variants 를 통해서 타겟 variant를 얻어 제공함.
    '''
    variant_metrics_list = variant_db.get_variant_metrics()
    # print(json.dumps(variant_metrics_list, indent=2))    

    response = test_thompson_sampling_w_variants(variant_metrics_list,trial=1) 
    target_variant = response[0]
    return target_variant

#########################################

def api_predict(i, endpoint_name, batch_size,input_batch_element,test_batch_element, variant_db, verbose=False):
    '''
    Dynamic AB Testing 의 메힌 함수로서, 톰슨 샘플링을 통한 Target Varient 제공, 추론, 리워드 저장에 대한 함수 임.
    '''
    def api_invocation(i, input_batch_element, variant_name):
        '''
        배치 사이즈 만큼 추론을 하고, 호출 기록을 variant_db 에 저장 함.
        '''
        test_preds = predict_with_db(endpoint_name, variant_name, input_batch_element, batch_size, variant_db) 

        return test_preds
    
    def api_conversion(variant_name, conversion, reward, variant_db):    
        '''
        해당 변형에 conversion, reward 를 업데이트 함 (1 씩  더함)
        '''
        variant_record = variant_db.update_variant(variant_name = variant_name, 
                                            invocation=0, 
                                            conversion=conversion, 
                                            reward=reward, 
                                            verbose=False
                                            )

    # MAB 알고리즘에 따른 대상 변형을 얻기
    variant_name = get_target_variant(variant_db)
    if verbose:
        print("\n##################################")
        print("\nvariant_name: ", variant_name)
        
    # 대상 변형에 추론 결과 얻기    
    result = api_invocation(i, input_batch_element, variant_name)

    if len(result) > 0 :
        predictions = result
        pred_df = join_test(test_batch_element.reset_index(drop=True), predictions, variant_name)      
            
        # 메타 정보를 위해서 아래 batch, invocattion and reward 정보 저장
        pred_df['strategy'] = "TomsonSampling"
        pred_df['batch'], pred_df['invocation'] = i, 1
#         # Set the reward based on prediction having a probability above a threshold
        pred_df['reward'] = pred_df.apply(lambda r: r['is_helpful'] == r['is_helpful_prediction'], axis=1).astype(int)
    

#         # is_helpful_prediction, is_helpful_prob 로 정렬을 한 후에 Top 1 만을 선택 함.
        pred_top = pred_df.sort_values(['is_helpful_prediction', 'is_helpful_prob'], ascending=False).head(1)
        reward = float(pred_top['reward'].sum())
        
        if verbose:
            # print("\nPrediction with meta data")
            # dp(pred_df)
            print("Top predicton with meta data")
            dp(pred_top)

        
        
#         # reward = 1 을 더하는 함수 임.
        if reward > 0:
            api_conversion(variant_name, conversion=1, reward=reward, 
                           variant_db=variant_db)               
            
            if verbose:
                print("--> Reward and conversion are recoded in variant_db: ")
                
        return pred_top
    else:
        print('error, no predictions', result)

#########################################
        
def delete_endpoint(client, endpoint_name ,is_del_model=True):
    '''
    model, EndpointConfig, Endpoint 삭제
    '''
    response = client.describe_endpoint(EndpointName=endpoint_name)
    EndpointConfigName = response['EndpointConfigName']
    
    response = client.describe_endpoint_config(EndpointConfigName=EndpointConfigName)
    model_name = response['ProductionVariants'][0]['ModelName']    

#     print("EndpointConfigName: \n", EndpointConfigName)
#     print("model_name: \n", model_name)    

    if is_del_model: # 모델도 삭제 여부 임.
        client.delete_model(ModelName=model_name)    
        
    client.delete_endpoint(EndpointName=endpoint_name)
    client.delete_endpoint_config(EndpointConfigName=EndpointConfigName)    
    
    print(f'--- Deleted model: {model_name}')
    print(f'--- Deleted endpoint: {endpoint_name}')
    print(f'--- Deleted endpoint_config: {EndpointConfigName}')    
