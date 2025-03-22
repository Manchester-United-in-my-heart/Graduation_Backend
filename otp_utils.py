import os
from dotenv import load_dotenv, dotenv_values
import pyotp
import qrcode

load_dotenv()

def get_otp_auth_string():
    otp_secret = os.getenv("OTP_SECRET_KEY")  
    otp_auth_string = pyotp.TOTP(otp_secret).provisioning_uri(name="Khamtheadmin", issuer_name="Admin")
    return otp_auth_string

def get_qr_code():
    qrcode.make(get_otp_auth_string()).save("otp_qr_code.png")
    # totp_qr = pyotp.TOTP(os.getenv("OTP_SECRET_KEY"))
    
    return {
        "message": "QR code generated successfully"
    }
    
def verify_otp(otp):
    otp_secret = os.getenv("OTP_SECRET_KEY")
    totp = pyotp.TOTP(otp_secret)
    return totp.verify(otp)