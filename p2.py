class Persona:
    def __init__(self, age: int, name: str):
        self.age = age
        self.name = name

    def say_hi(self):
        print(f"Hi, my name is {self.name} and I am {self.age} years old")

p = Persona(1, "Mario")
p.say_hi()

p2 = Persona(2, "Luigi")
p2.say_hi()


import pandas as pd

a = pd.DataFrame([1,2,3])
