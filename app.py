from flask import Flask, request, render_template
from flask_restful import reqparse, abort, Api, Resource
from flask_cors import CORS
import json
import datetime
import pymysql

app = Flask(__name__)
api = Api(app)
cors = CORS(app)

parser = reqparse.RequestParser()
parser.add_argument('car_id', type=str)
parser.add_argument('team_name', type=str)
parser.add_argument('penalty', type=str)
parser.add_argument('timestamp', type=str)
parser.add_argument('cur_job', type=str)
parser.add_argument('status', type=str)

# 데이터베이스 정보 설정
DB = ''
USER = ''
PASSWORD = ''
HOST = ''


# 현재 주행중인 차량 ID 저장 / 불러오기
def save_car_id_to_file(value):
    f = open("car_id.txt", "w")
    f.write(str(value))
    f.close()

def read_car_id_from_file():
    f = open("car_id.txt")
    a = f.read()
    f.close()
    return int(a)

# 주행중 / 미 주행중 판별용 파일 저장 / 불러오기
def save_car_run_status_to_file(value):
    f = open("run_status.txt", "w")
    f.write(str(value))
    f.close()

def read_car_run_status_from_file():
    f = open("run_status.txt")
    a = f.read()
    f.close()
    return int(a)

# datetime 두개를 가지고 차이 구해서 문자열로 return 하는 함수. penalty 포함 계산 가능
def datetime_sub_result(first, second, penalty=0):
    second += datetime.timedelta(seconds=penalty)
    temp = second - first
    minutes = ((second - first).seconds // 60) % 60
    seconds = (second - first).seconds % 60
    microseconds = (second - first).microseconds
    return datetime.datetime(1, 1, 1, 0, minutes, seconds, microseconds).strftime("%M분 %S초 %f")[:-3]

# DB에 시간 업데이트 하는 용도의 API
# car_id: 차량 번호, current_job: 현재 바퀴 정보, timestamp: 시간
class SetTime(Resource):
    def post(self):
        try:
            args = parser.parse_args()
            car_id = args['car_id']
            current_job = int(args['cur_job'])
            timestamp = args['timestamp']
            db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')
            cursor = db.cursor(pymysql.cursors.DictCursor)
            # 출발
            if current_job == 0:
                sql = "UPDATE contest SET startTimeStamp = %s WHERE carID = %s AND startTimeStamp IS NULL;"
            # 첫바퀴 돌고옴
            elif current_job == 1:
                sql = "UPDATE contest SET firstLapTimeStamp = %s WHERE carID = %s AND firstLapTimeStamp IS NULL;"
            # 두번째 바퀴 돌고옴
            elif current_job == 2:
                sql = "UPDATE contest SET secondLapTimeStamp = %s WHERE carID = %s AND secondLapTimeStamp IS NULL;"
            # 세번째 바퀴 돌고옴
            else:
                sql = "UPDATE contest SET thirdLapTimeStamp = %s WHERE carID = %s AND thirdLapTimeStamp IS NULL;"
            # DB에 저장
            res = cursor.execute(sql, (timestamp, str(car_id)))
            cursor.close()
            db.commit()
            db.close()
            if res:
                return {"result": "success"}
            else:
                return {"result": "failure"}
        except:
            return {"result": "failure"}

# 페널티 업데이트 API
# car_id: 차량 번호, penalty: 페널티 증감량
class UpdatePenalty(Resource):
    def post(self):
        try:
            args = parser.parse_args()
            car_id = args['car_id']
            penalty = args['penalty']
            db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')
            cursor = db.cursor(pymysql.cursors.DictCursor)
            sql = "UPDATE contest SET penalty = penalty + %s WHERE carID = %s;"
            res = cursor.execute(sql, (penalty, car_id))
            cursor.close()
            db.commit()
            db.close()
            if res:
                return {"result": "success"}
            else: 
                print(res)
                return {"result": "failure"}
        except:
            return {"result": "failure"}

# 실격 처리 API
# car_id: 차량 번호
class SetDQ(Resource):
    def post(self):
        try:
            args = parser.parse_args()
            car_id = args['car_id']
            db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')
            cursor = db.cursor(pymysql.cursors.DictCursor)
            sql = "UPDATE contest SET disqualified=1 WHERE carID = %s AND disqualified=0;" 
            res = cursor.execute(sql, (car_id))
            cursor.close()
            db.commit()
            db.close()
            if res:
                if read_car_id_from_file() == int(car_id):
                    save_car_id_to_file(-1)
                    save_car_run_status_to_file(0)
                return {"result": "success"}
            else:
                return {"result": "failure"}
        except:
            return {"result": "failure"}

# 주행할 차량 등록 API
# car_id: 차량 번호, team_name: 팀 이름
class SetCurrentCar(Resource):
    def post(self):
        args = parser.parse_args()
        car_id = args['car_id']
        team_name = args['team_name']
        print(car_id, team_name)
        try:
            db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')
            cursor = db.cursor(pymysql.cursors.DictCursor)
            sql = "DELETE FROM contest WHERE carID = %s;"
            cursor.execute(sql, (car_id))
            db.commit()
            cursor.close()
            cursor = db.cursor(pymysql.cursors.DictCursor)
            sql = "INSERT INTO contest(carID, teamName) VALUES(%s, %s);"
            res = cursor.execute(sql, (car_id, team_name))
            db.commit()
            cursor.close()
            db.close()
            if res:
                try:
                    save_car_id_to_file(int(car_id))
                except:
                    return {"result": "failure"}
                print("Current Car ID changed:", int(car_id))
                return {"result": "success"}
            else:
                return {"result": "failure"}
        except:
            return {"result": "failure"}

# 주행 완료시 호출하는 API
class SetFinished(Resource):
    def post(self):
        save_car_id_to_file(-1)
        return {"result": "success"}

# 웹페이지에서 DB 데이터 호출용으로 사용하는 API
# DB 데이터를 기반으로 랩타임 계산 후 return
class GetData(Resource):
    def get(self):
        try:
            db = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')
            cursor = db.cursor(pymysql.cursors.DictCursor)
            sql = "SELECT * FROM contest;"
            cursor.execute(sql);
            db.commit()
            return_list = []
            results = cursor.fetchall()
            cursor.close()
            db.close()
            for result in results:
                # print(result)
                start = result["startTimeStamp"]
                lap_one = result["firstLapTimeStamp"]
                lap_two = result["secondLapTimeStamp"]
                lap_three = result["thirdLapTimeStamp"]
                null_time = datetime.datetime(1, 1, 1, 0, 0, 0, 0)
                
                if lap_three is not None:
                    return_list.append({"carID": result["carID"], 
                                        "teamName": result["teamName"], 
                                        "firstLapTime": datetime_sub_result(start, lap_one), 
                                        "secondLapTime": datetime_sub_result(lap_one, lap_two),
                                        "thirdLapTime": datetime_sub_result(lap_two, lap_three),
                                        "totalLapTime": "59분 59초 999" if int(result["disqualified"]) == 1 else datetime_sub_result(start, lap_three, int(result["penalty"])),
                                        "penalty": str(result["penalty"]) + "초",
                                        "disqualified": result["disqualified"]})
                elif lap_two is not None:
                    return_list.append({"carID": result["carID"], 
                                        "teamName": result["teamName"], 
                                        "firstLapTime": datetime_sub_result(start, lap_one), 
                                        "secondLapTime": datetime_sub_result(lap_one, lap_two),
                                        "thirdLapTime": null_time.strftime("%M분 %S초 %f")[:-3],
                                        "totalLapTime": "59분 59초 999" if int(result["disqualified"]) == 1 else datetime_sub_result(start, lap_two, int(result["penalty"])),
                                        "penalty": str(result["penalty"]) + "초",
                                        "disqualified": result["disqualified"]})
                elif lap_one is not None:
                    return_list.append({"carID": result["carID"], 
                                        "teamName": result["teamName"], 
                                        "firstLapTime": datetime_sub_result(start, lap_one), 
                                        "secondLapTime": null_time.strftime("%M분 %S초 %f")[:-3], 
                                        "thirdLapTime": null_time.strftime("%M분 %S초 %f")[:-3],
                                        "totalLapTime": "59분 59초 999" if int(result["disqualified"]) == 1 else datetime_sub_result(start, lap_one, int(result["penalty"])),
                                        "penalty": str(result["penalty"]) + "초",
                                        "disqualified": result["disqualified"]})
                else:
                    return_list.append({"carID": result["carID"], 
                                        "teamName": result["teamName"], 
                                        "firstLapTime": null_time.strftime("%M분 %S초 %f")[:-3], 
                                        "secondLapTime": null_time.strftime("%M분 %S초 %f")[:-3], 
                                        "thirdLapTime": null_time.strftime("%M분 %S초 %f")[:-3], 
                                        "totalLapTime": "59분 59초 999" if int(result["disqualified"]) == 1 else datetime_sub_result(null_time, null_time, int(result["penalty"])),
                                        "penalty": str(result["penalty"]) + "초",
                                        "disqualified": result["disqualified"]})
            
            return return_list
        except:
            return []

# 현재 주행중인 차량 번호 확인용 API
class CarID(Resource):
    def get(self):
        return read_car_id_from_file()

# 현재 기록 측정중인지 여부 확인용 API
class RunStatus(Resource):
    def get(self):
        return read_car_run_status_from_file()

    def post(self):
        try:
            args = parser.parse_args()
            status = args["status"]
            save_car_run_status_to_file(int(status))
            return {"result": "success"}
        except:
            return {"result": "failure"}

api.add_resource(GetData, '/getdata')
api.add_resource(CarID, '/getid')
api.add_resource(SetCurrentCar, '/setcar')
api.add_resource(SetFinished, '/setfinished')
api.add_resource(SetDQ, '/setdq')
api.add_resource(UpdatePenalty, '/updatepenalty')
api.add_resource(SetTime, '/settime')
api.add_resource(RunStatus, '/status')


if __name__ == "__main__":
    try:
        save_car_id_to_file(-1)
        save_car_run_status_to_file(0)
        app.run(debug=True, host='0.0.0.0')
    except:
        print("EXIT")
        
