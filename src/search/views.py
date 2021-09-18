from django.shortcuts import render

from classes.models import Classes

from mainpage.views import init_render_dict


# ====================================================================
# /search
# ====================================================================

def search(request):
    t_dict = init_render_dict(request)

    query = request.GET.get("q", "")

    results = (Classes.objects.filter(name__icontains=query)
               | Classes.objects.filter(description__icontains=query))

    t_dict["results"] = results

    return render(request, "search.html", t_dict)
