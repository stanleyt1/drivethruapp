import os
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit



engine = create_engine(os.getenv("DATABASE_URL"))
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

socketio = SocketIO(app)

db = scoped_session(sessionmaker(bind=engine)) 

@app.route("/")
def home():
    orders = db.execute("select orders.*, deliveries.service, deliveries.customer from orders left outer join deliveries on orders.id = deliveries.order_id order by orders.id asc")
    return render_template("index.html", orders = orders)


@app.route("/new", methods = ["GET", "POST"])
def new():
    if(request.method == "POST"):
        name = request.form.get("name").title()
        number = request.form.get("number")
        number = number[0:3] + "-"  + number[3:6]  + "-" + number[6:10]
        print(number)
        car = request.form.get("car").title()
        order = request.form.get("order")
        payment = request.form.get("payment")
        print(f"Name: {name}  Number:{number} Car: {car} Order:{order} Payment:{payment}")
        if(order == ""):
            print("No Order Info")
            db.execute("INSERT INTO orders (name, number, car, payment, status, time) VALUES (:name, :number, :car, :payment, 'IP', :time)", 
            {"name":name, "number":number, "car":car, "payment":payment, "time" : int(time.time())})
            db.commit()
            print("done")
        else:
            db.execute("INSERT INTO orders (name, number, car, payment, order_info, status, time) VALUES (:name, :number, :car, :payment, :order_info, 'IP', :time)", 
            {"name":name, "number":number, "car":car, "payment":payment, "order_info": order, "time":int(time.time())})
            db.commit()
            print("done")
        return render_template("new.html")
    else:
        return render_template("new.html")


@app.route("/past")
def past():
    orders = db.execute("select orders.*, deliveries.service, deliveries.customer from orders left outer join deliveries on orders.id = deliveries.order_id order by orders.id desc")
    return render_template("past.html", orders = orders)


@app.route("/delivery", methods = ["GET", "POST"])
def delivery():
    if(request.method == "POST"):
        service = request.form.get("service")
        customer = request.form.get("customer").title()
        carDelivery = request.form.get("carDelivery").title()

        db.execute("INSERT INTO orders (name, number, car, payment, order_info, status, time) VALUES ('Delivery', 'NA', :car, 'Paid', 'NA', 'IP', :time)",
        {"car" :carDelivery, "time" :int(time.time()) } )
        db.commit()
        currDelivery = db.execute("SELECT * from orders where name = 'Delivery' order by id desc limit 1")
        print(currDelivery)
        order_id = 0
        for d in currDelivery:
            order_id = d.id
    
        db.execute("INSERT INTO deliveries (order_id, service, car, customer) VALUES (:order_id, :service, :carDelivery, :customer)",
        {"order_id":order_id,"service" : service, "carDelivery" :carDelivery, "customer" : customer})
        db.commit()
    

        return render_template("delivery.html")
    return render_template("delivery.html")

@app.route("/update", methods = ["POST"])
def update():
    id = request.form.get("data")
    typeOfData = request.form.get("type")
    print(typeOfData)
    print(id)
    if(typeOfData == "paid"):
        db.execute("update orders set payment = 'Paid' where id = :id ", 
        {"id":id})
        db.commit()
    if(typeOfData == "complete"):
        db.execute("update orders set status = 'C' where id = :id ", 
        {"id":id})
        db.execute("update orders set payment = 'Paid' where id = :id ", 
        {"id":id})
        db.commit()
        
    return "Sucess"

@socketio.on("reload")
def reload():
    print("ReloadEveryone")
    emit("reload page", broadcast = True)