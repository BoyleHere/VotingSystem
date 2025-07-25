import random

def send_otp():
    return str(random.randint(100000, 999999))  # Generates a 6-digit OTP

def register_voter(aadhar_number):
    otp = send_otp()
    # Assume sending OTP to the registered mobile number
    print(f"OTP sent to registered mobile number: {otp}")
    return 'OTP sent for verification.'

def authenticate_voter(otp):
    # For demo, assume correct OTP is "123456"
    if otp == "123456":
        return 'Authentication successful.'
    else:
        return 'Invalid OTP. Authentication failed.'