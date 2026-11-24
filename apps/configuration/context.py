from .models import Campground


def campground(request):
    return {"campground": Campground.current()}
