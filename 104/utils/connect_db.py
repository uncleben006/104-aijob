import os
from dotenv import load_dotenv
from pymongo import MongoClient

# 載入 .env 檔案中的環境變數
load_dotenv()

def connect_db():
    """
    連線到 MongoDB 資料庫
    """

    ENV = os.getenv("ENV", "dev")
    MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
    MONGO_PORT = os.getenv("MONGO_PORT", "27017")
    MONGO_INITDB_ROOT_USERNAME = os.getenv("MONGO_INITDB_ROOT_USERNAME", "root")
    MONGO_INITDB_ROOT_PASSWORD = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "root")
    if ENV == "local":
        uri = f"mongodb://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
    else:
        uri = f"mongodb+srv://{MONGO_INITDB_ROOT_USERNAME}:{MONGO_INITDB_ROOT_PASSWORD}@{MONGO_HOST}"
    return MongoClient(uri)

def jobs_detail_project():
    """
    處理 jobs_detail 集合中的資料，將需要的欄位提取出來
    """

    return {
        '$project': {
            '_id': 0, 
            'link': '$_id', 
            'job': '$header.jobName', 
            'company': '$header.custName', 
            'address': '$jobDetail.addressRegion', 
            'industry': '$industry', 
            'salary': '$jobDetail.salary', 
            'salaryType': '$jobDetail.salaryType',
            # 若 employees 為 "暫不提供"，則設為 0；否則去除字串中的 "人" 並轉換成數字
            'employees': {
                '$cond': {
                    'if': { '$eq': ['$employees', '暫不提供'] },
                    'then': 0,
                    'else': {
                        '$toInt': {
                            '$replaceAll': {
                                'input': '$employees',
                                'find': '人',
                                'replacement': ''
                            }
                        }
                    }
                }
            },
            # 將 specialty 陣列中每個項目的 description 組合成一個字串，以逗號分隔
            'specialty': {
                '$reduce': {
                    'input': {
                        '$map': {
                            'input': '$condition.specialty',
                            'as': 'item',
                            'in': '$$item.description'
                        }
                    },
                    'initialValue': '',
                    'in': {
                        '$concat': [
                            '$$value',
                            {
                                '$cond': [
                                    { '$eq': ['$$value', ''] },
                                    '',
                                    ', '
                                ]
                            },
                            '$$this'
                        ]
                    }
                }
            },
            # 將 skill 陣列中每個項目的 description 組合成一個字串，以逗號分隔
            'skill': {
                '$reduce': {
                    'input': {
                        '$map': {
                            'input': '$condition.skill',
                            'as': 'item',
                            'in': '$$item.description'
                        }
                    },
                    'initialValue': '',
                    'in': {
                        '$concat': [
                            '$$value',
                            {
                                '$cond': [
                                    { '$eq': ['$$value', ''] },
                                    '',
                                    ', '
                                ]
                            },
                            '$$this'
                        ]
                    }
                }
            },
            # 換算年薪，時薪、日薪不計算，月薪乘 12 計算
            'annualSalary': {
                '$switch': {
                    'branches': [
                        {
                            'case': { '$eq': ['$jobDetail.salaryType', 10] },
                            'then': 0
                        },
                        {
                            'case': { '$eq': ['$jobDetail.salaryType', 50] },
                            'then': {
                                '$let': {
                                    'vars': {
                                        'cleaned': {
                                            '$reduce': {
                                                'input': ['月薪', '元以上', '元', ','],
                                                'initialValue': '$jobDetail.salary',
                                                'in': {
                                                    '$replaceAll': {
                                                        'input': '$$value',
                                                        'find': '$$this',
                                                        'replacement': ''
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'in': {
                                        '$multiply': [
                                            {
                                                '$let': {
                                                    'vars': {
                                                        'parts': { '$split': ['$$cleaned', '~'] }
                                                    },
                                                    'in': {
                                                        '$cond': [
                                                            { '$gt': [{ '$size': '$$parts' }, 1] },
                                                            {
                                                                '$avg': {
                                                                    '$map': {
                                                                        'input': '$$parts',
                                                                        'as': 'p',
                                                                        'in': { '$toDouble': '$$p' }
                                                                    }
                                                                }
                                                            },
                                                            { '$toDouble': { '$arrayElemAt': ['$$parts', 0] } }
                                                        ]
                                                    }
                                                }
                                            },
                                            12
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            'case': { '$eq': ['$jobDetail.salaryType', 60] },
                            'then': {
                                '$let': {
                                    'vars': {
                                        'cleaned': {
                                            '$reduce': {
                                                'input': ['年薪', '元以上', '元', ','],
                                                'initialValue': '$jobDetail.salary',
                                                'in': {
                                                    '$replaceAll': {
                                                        'input': '$$value',
                                                        'find': '$$this',
                                                        'replacement': ''
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'in': {
                                        '$let': {
                                            'vars': {
                                                'parts': { '$split': ['$$cleaned', '~'] }
                                            },
                                            'in': {
                                                '$cond': [
                                                    { '$gt': [{ '$size': '$$parts' }, 1] },
                                                    {
                                                        '$avg': {
                                                            '$map': {
                                                                'input': '$$parts',
                                                                'as': 'p',
                                                                'in': { '$toDouble': '$$p' }
                                                            }
                                                        }
                                                    },
                                                    { '$toDouble': { '$arrayElemAt': ['$$parts', 0] } }
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    'default': None
                }
            },
            'other': '$condition.other',
            'detail': '$jobDetail.jobDescription'
        }
    }