"""
Project's entry-point
"""
import logging.config
import os
import json
import yaml

from tavern.core import run

token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE1MzIwOTQ4MzcsImlzcyI6Ik9ueXhwcmV2IiwiZXhwIjoxNTMyMTM4MDM3LCJuYmYiOjE1MzIwOTQ4MzYsImRhdGEiOnsiYXBwIjp7ImFwaUlkIjoiODNjYzEyYTVmY2M1IiwiYXBwQ29kIjoxMiwiYXBwT3NDb2QiOjEsIm5hbWUiOiJSZWNhZCIsImFwaWtleSI6IjgzY2MxMmE1ZmNjNSIsInNlY3VyaXR5IjoiSSIsImxhdW5jaGVySWdub3JlIjoiTiIsImNhY2hlIjoiSSIsInZlcnNpb24iOiIxLjAuMCJ9LCJ1c2VyIjp7InBmQ29kIjoxLCJ1c3VhcmlvQ29kIjoxLCJvcmdhb0NvZCI6MSwib3JnYW9FbnRpZGFkZUNvZCI6MSwicHJpdkNvZCI6MTUsInN1cGVyVXN1YXJpbyI6IlMiLCJub21lIjoiRkVMSVBIRSBBVUdVU1RPIEJVRU5PIiwidXVpZCI6IjQxNDhkOTM4NWUyMTgxMTQzNmMxZDBmNjQ3NjE5MyIsImxvZ2luIjoiMDI0MDE2MjcxNDYiLCJmb3RvIjoiaHR0cHM6XC9cL3N0b3JhZ2Uub255eGVycC5jb20uYnJcLzhkOTBkNmY1ZDM1YjQ3NzlmMjM1NTY2NDNhM2YyZS5wbmciLCJjZWx1bGFyIjpudWxsLCJlbWFpbCI6bnVsbCwidXNlci1sZW5ndGgiOjgsInBmaWQiOiI0Nzc5MDU1OTMzMDg3MzAyODA5Iiwib2lkIjoiM2E5NWMzZTI0NGUzOTBlN2NhOGNlZDZkM2FiYzBiIiwib2VpZCI6IjVlOTU3NjdmMWFjNTVmODFjNWM0ZGQ5YWUyMTBlMyIsImZ1c29Ib3JhcmlvIjoiLTMiLCJtb2VkYSI6ImJyYXppbGlhbl9yZWFsIiwiaWRpb21hIjoicHQtYnIiLCJkYXRhIjoiYnJhemlsaWFuX2RhdGVfZm9ybWF0IiwibGF1bmNoZXIiOiJfYmxhbmsifX19.-deN23V6C_KH-BS2nbLDNeMHdugxdLvaUe_yzRsI-r8'

# Carrega os JWTs(app and user)
os.environ.update({
    "APP_TOKEN": token,
    "USER_TOKEN": token,
    "USER_TOKEN_NO_AUTH": token,
    "URL_API": "https://protokol-api.onyxapis.com"
})

with open("tests/logging.yaml", "r") as spec_file:
    settings = yaml.load(spec_file)
    logging.config.dictConfig(settings)

test_info = run('tests/main.tavern.yaml')
pass
print(json.dumps(test_info))

exit(int(test_info['all_passed'] is False))
