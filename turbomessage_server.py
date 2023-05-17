import grpc
import turbomessage_pb2
import turbomessage_pb2_grpc
from concurrent import futures
import threading

class MessageService(turbomessage_pb2_grpc.TurboMessageServicer):
    user_db = {}  # database of users with usernames as keys and email arrays as values
    outbox_db = {}  # database of outbox with usernames as keys and email arrays as values
    users = []

    max_num_emails = 5
    email_id_counter = 0

    lock_registerUser = threading.Lock()
    lock_send_email = threading.Lock()
    lock_delete_inbox_email = threading.Lock()
    lock_delete_outbox_email = threading.Lock()
    lock_read_inbox_emails = threading.Lock()
    lock_read_outbox_emails = threading.Lock()
    lock_mark_email_as_read = threading.Lock()

    def checkUser(self, request, context):
        for user in MessageService.users:
            if (request.username == user.username) and (request.password == user.password):
                return turbomessage_pb2.Status(success=True, reason="Username and password are correct.")
        return turbomessage_pb2.Status(success=False, reason="Username or password is incorrect.")

    def registerUser(self, request, context):
        for user in MessageService.users:
            if (request.username == user.username):
                return turbomessage_pb2.Status(success=False, reason="Username has already been registered.")

        MessageService.lock_registerUser.acquire()
        MessageService.users.append(request)
        MessageService.user_db[request.username] = []
        MessageService.outbox_db[request.username] = []
        print(MessageService.users)
        MessageService.lock_registerUser.release()

        return turbomessage_pb2.Status(success=True, reason="User registered successfully.")
    
    def fetchInbox(self, request, context):
        user_emails = MessageService.user_db[request.username]
        inbox_response = turbomessage_pb2.FetchInboxResponse()
        inbox_response.emails.extend(user_emails)
        inbox_response.success = True
        return inbox_response

    def fetchSentMail(self, request, context):
        user_emails = MessageService.outbox_db[request.username]
        sent_mail_response = turbomessage_pb2.SentMailResponse()
        sent_mail_response.emails.extend(user_emails)
        sent_mail_response.success= True
        return sent_mail_response
    
    def sendEmail(self, request, context):
        recipient = request.recipient
        sender = request.sender

        for user in MessageService.users:
            if user.username == recipient:
                MessageService.lock_send_email.acquire()
                if len(MessageService.user_db[recipient]) >= MessageService.max_num_emails:
                    MessageService.lock_send_email.release()
                    return turbomessage_pb2.Status(success=False, reason="The recipient's inbox is full.")
                else:
                    new_email = turbomessage_pb2.Email(id=request.id, subject=request.subject, sender=request.sender, recipient=request.recipient, message=request.message, read=False)
                    MessageService.email_id_counter += 1
                    MessageService.user_db[recipient].append(new_email)
                    MessageService.outbox_db[sender].append(new_email)
                    MessageService.lock_send_email.release()
                    return turbomessage_pb2.Status(success=True, reason="Email sent successfully.")

        return turbomessage_pb2.Status(success=False, reason="Recipient user does not exist.")

    def read_inbox_emails(self, request, context):
        try:
            MessageService.lock_read_inbox_emails.acquire()
            user_emails = MessageService.user_db[request.username]
            for email in user_emails:
                yield email
            MessageService.lock_read_inbox_emails.release()
        except Exception:
            print("Error!")

    def read_outbox_emails(self, request, context):
        try:
            MessageService.lock_read_outbox_emails.acquire()
            user_emails = MessageService.outbox_db[request.username]
            for email in user_emails:
                yield email
            MessageService.lock_read_outbox_emails.release()
        except Exception:
            print(Exception)

    def mark_email_as_read(self, request, context):
        user_emails = MessageService.outbox_db[request.from_username]
        for i in range(0, len(user_emails)):
            if user_emails[i].email_id == request.email_id:
                MessageService.lock_mark_email_as_read.acquire()
                email_to_mark = user_emails[i]
                user_emails[i] = turbomessage_pb2.Email(email_id=email_to_mark.email_id, subject=email_to_mark.subject, from_username=email_to_mark.from_username, to_username=email_to_mark.to_username, body=email_to_mark.body, read=True)
                MessageService.lock_mark_email_as_read.release()
                return turbomessage_pb2.Status(success=True, reason="Email marked as read successfully.")
        return turbomessage_pb2.Status(success=False, reason="Email does not exist.")

    def delete_inbox_email(self, request, context):
        user_emails = MessageService.user_db[request.to_username]
        for i in range(0, len(user_emails)):
            if user_emails[i].email_id == request.email_id:
                MessageService.lock_delete_inbox_email.acquire()
                user_emails.pop(i)
                MessageService.lock_delete_inbox_email.release()
                return turbomessage_pb2.Status(success=True, reason="Email deleted successfully.")
        return turbomessage_pb2.Status(success=False, reason="Email does not exist.")

    def delete_outbox_email(self, request, context):
        user_emails = MessageService.outbox_db[request.from_username]
        for i in range(0, len(user_emails)):
            if user_emails[i].email_id == request.email_id:
                MessageService.lock_delete_outbox_email.acquire()
                user_emails.pop(i)
                MessageService.lock_delete_outbox_email.release()
                return turbomessage_pb2.Status(success=True, reason="Email deleted successfully.")
        return turbomessage_pb2.Status(success=False, reason="Email does not exist.")
    
    def deleteEmail(self, request, context):
        email_id = request.email_id
        for user in MessageService.users:
            emails = MessageService.user_db[user.username]
            for email in emails:
                if email.id == email_id:
                    emails.remove(email)
                    return turbomessage_pb2.DeleteEmailResponse(success=True, reason="Email deleted successfully.")
        
        return turbomessage_pb2.DeleteEmailResponse(success=False, reason="Email not found.")

    def readEmail(self, request, context):
        user_emails = MessageService.user_db[request.recipient]
        for email in user_emails:
            if email.id == request.id:
                email.read = True
                return turbomessage_pb2.ReadEmailResponse(success=True, email=email)
        return turbomessage_pb2.ReadEmailResponse(success=False, reason="Email not found.")
        
def start_message_server():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    turbomessage_pb2_grpc.add_TurboMessageServicer_to_server(MessageService(), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    print("Starting Message Server...")
    start_message_server()
