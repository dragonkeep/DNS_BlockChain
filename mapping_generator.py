from faker import Faker
import json
import random

fake = Faker()
fake.seed(4321)

record_len = 100
records = []

# 定义DNS记录类型和对应的生成函数
def generate_a_record(domain):
    return {
        'host': domain,
        'type': 'A',
        'value': fake.ipv4()
    }

def generate_cname_record(domain):
    return {
        'host': domain,
        'type': 'CNAME',
        'value': f'alias-{fake.domain_name()}'
    }

def generate_mx_record(domain):
    priority = random.randint(1, 20)
    return {
        'host': domain,
        'type': 'MX',
        'value': [f'mx{priority}.{domain}', priority]
    }

def generate_ns_record(domain):
    return {
        'host': domain,
        'type': 'NS',
        'value': f'ns{random.randint(1,3)}.{domain}'
    }

def generate_txt_record(domain):
    return {
        'host': domain,
        'type': 'TXT',
        'value': fake.text(max_nb_chars=100)
    }

def generate_soa_record(domain):
    return {
        'host': domain,
        'type': 'SOA',
        'value': [f'ns1.{domain}', f'admin.{domain}']
    }

# 生成不同类型的DNS记录
for i in range(record_len):
    domain = fake.domain_name()
    
    # 为每个域名生成一组DNS记录
    records.append(generate_a_record(domain))
    
    # 随机添加其他类型的记录
    record_types = [
        generate_cname_record,
        generate_mx_record,
        generate_ns_record,
        generate_txt_record
    ]
    
    # 为每个域名随机添加2-4个其他类型的记录
    for _ in range(random.randint(2, 4)):
        record_func = random.choice(record_types)
        records.append(record_func(domain))
    
    # 每个域名都添加一个SOA记录
    records.append(generate_soa_record(domain))

# 将记录转换为JSON格式并写入文件
record_json = json.dumps(records, indent=2)

with open('sample_mapping', mode='w') as f:
    f.write(record_json)

