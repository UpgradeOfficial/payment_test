from .models import User
import random


def create_test_user():
    email = f"a{random.randint(0, 1000000000000000)}@b.c"
    user = User.objects.create_user(
        email=email,
        username=email,
        password="aaaaaaaaaa",
        
    )
    return user
