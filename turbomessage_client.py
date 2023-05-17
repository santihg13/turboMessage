import grpc
import os
import sys
import turbomessage_pb2
import turbomessage_pb2_grpc
import random

class TurboMessageClient():
    max_emails = 5

    def __init__(self, target):
        self.target = target
        self.channel = grpc.insecure_channel(target)
        self.stub = turbomessage_pb2_grpc.TurboMessageStub(self.channel)

    def clear_screen(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def show_initial_page(self):
        self.clear_screen()
        print((" " * 30) + "Welcome to TurboMessage")
        print("Log in with existing user - 1")
        print("Register new user - 2")

        flag = True
        while flag:
            decision = input("Enter the number of the option you want -> ")
            if decision == '1':
                self.show_login_page()
                flag = False
            elif decision == '2':
                self.show_registration_page()
                flag = False
            else:
                print("Invalid option. Please try again.\n")

    def show_login_page(self):
        self.clear_screen()
        print((" " * 30) + "Login Page")

        while True:
            username = input("Enter your username: ")
            password = input("Enter your password: ")

            potential_user = turbomessage_pb2.User(username=username, password=password)
            response = self.stub.checkUser(potential_user)
            if response.success == True:
                self.user = potential_user
                self.clear_screen()
                self.show_inbox()
                break
            else:
                print(response.reason + "\n")
            
            while True:
                decision = input("Do you want to go back to the initial page? (y/n) -> ")
                if decision == "y":
                    self.clear_screen()
                    self.show_initial_page()
                    break
                elif decision == "n":
                    break


    def show_registration_page(self):
        self.clear_screen()
        print((" " * 30) + "Registration Page") 

        while True:
            username = input("Enter the username you want to register: ")
            password = input("Enter the password you want to use: ")

            potential_user = turbomessage_pb2.User(username=username, password=password)
            response = self.stub.registerUser(potential_user)
            if response.success == True:
                self.user = potential_user
                self.clear_screen()
                self.show_inbox()
                break
            else:
                print(response.reason + "\n")
            
            while True:
                decision = input("Do you want to go back to the initial page? (y/n) -> ")
                if decision == "y":
                    self.clear_screen()
                    self.show_initial_page()
                    break
                elif decision == "n":
                    break

    def show_inbox(self):
        print((" " * 30) + "Welcome " + self.user.username)
        self.fetch_inbox()
        print()
        self.fetch_sent_mail()
        print()
        print("Actions to Perform:")
        print((" " * 4) + "1. Compose a new email")
        print((" " * 4) + "2. Read an email")
        print((" " * 4) + "3. Delete an email")
        print((" " * 4) + "4. Refresh inbox")
        print((" " * 4) + "5. Exit TurboMessage")
        print()

        flag = True
        while flag:
            decision = input("Enter the number of the action you want to perform -> ")
            if decision == '1':
                self.compose_email()
            elif decision == '2':
                self.read_email()
            elif decision == '3':
                self.delete_email()
            elif decision == '4':
                self.fetch_inbox()
            elif decision == '5':
                flag = False
            else:
                print("Invalid option. Please try again.\n")

    def compose_email(self):
        self.clear_screen()
        print((" " * 30) + "Compose Email")
        recipient = input("Enter the recipient's username: ")
        subject = input("Enter the email subject: ")
        message = input("Enter the email body: ")

        email = turbomessage_pb2.Email(
            id= random.randint(10,200)*random.randint(10,200),
            sender=self.user.username,
            recipient=recipient,
            subject=subject,
            message=message, 
            read= False
        )

        response = self.stub.sendEmail(email)
        if response.success:
            print("Email sent successfully!\n")
        else:
            print("Failed to send email. Reason: " + response.reason + "\n")

    def read_email(self):
        self.clear_screen()
        print((" " * 30) + "Read Email")
        email_id = input("Enter the ID of the email you want to read: ")

        email = turbomessage_pb2.ReadEmailRequest(
            id=int(email_id),
            recipient=self.user.username
        )

        response = self.stub.readEmail(email)
        if response.success:
            print("Email Details:")
            print("From: " + response.email.sender)
            print("Subject: " + response.email.subject)
            print("Body: " + response.email.message + "\n")
        else:
            print("Failed to read email. Reason: " + response.reason + "\n")

    def delete_email(self):
        self.clear_screen()
        print((" " * 30) + "Delete Email")
        email_id = input("Enter the ID of the email you want to delete: ")

        #email = turbomessage_pb2.Email(
        #    id=int(email_id),
        #    recipient=self.user.username
        #)

        request = turbomessage_pb2.DeleteEmailRequest(email_id=int(email_id))
        response = self.stub.deleteEmail(request)
        if response.success:
            print("Email deleted successfully!\n")
        else:
            print("Failed to delete email. Reason: " + response.reason + "\n")

    def fetch_inbox(self):
        request = turbomessage_pb2.FetchInboxRequest(username=self.user.username)
        response = self.stub.fetchInbox(request)
        if response.success:
            print("Inbox:")
            for email in response.emails:
                print("ID: " + str(email.id))
                print("From: " + email.sender)
                print("Subject: " + email.subject)
                print("Body: " + email.message)
                print()
        else:
            print("Failed to fetch inbox. Reason: " + response.reason + "\n")

    def fetch_sent_mail(self):
        sent_mail_request = turbomessage_pb2.SentMailRequest(username=self.user.username)
        response = self.stub.fetchSentMail(sent_mail_request)

        if response.success:
            print("Sent Mail:")
            for email in response.emails:
                print("ID: " + str(email.id))
                print("To: " + email.recipient)
                print("Subject: " + email.subject)
                print("Body: " + email.message)
                print()
        else:
            print("Failed to fetch sent mail. Reason: " + response.reason + "\n")
if __name__ == "__main__":
    target = 'localhost:50051'
    client = TurboMessageClient(target)
    client.show_initial_page()