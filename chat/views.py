from django.shortcuts import render

# Create your views here.


def index(request):
	return render(request, 'chat/index.html', {})

def room(request, room_name):
	return render(request, 'chat/room.html', {
		'room_name': room_name
	})

def adminroom(request, room_name):
	
	if request.user.is_authenticated and request.user.is_superuser:
		admin = True

	else:
		admin = False


	context = {'room_name' : room_name, 
				'admin': admin }
	return render(request, 'chat/admin_room.html', context)