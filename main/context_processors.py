def nav_section(request):
    return {"nav_section": request.path_info.strip("/").split("/")[0]}
