from django.shortcuts import render

from classes.models import Classes


# ====================================================================
# /search
# ====================================================================

def search(request):
    query = request.GET.get("q", "")

    results = (Classes.objects.filter(name__icontains=query)
               | Classes.objects.filter(description__icontains=query))

    return render(request, "search.html", {"results": results})
