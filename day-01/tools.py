# tools.py


ue_error_db = [
    {
        "error": "Accessed None trying to read property",

        "reason":
        "The object reference is nullptr. The UObject or variable has not been initialized.",

        "solution":
        """
1. Check whether the object is valid.
2. Use IsValid() before accessing UObject.
3. Check BeginPlay initialization order.
4. Verify GameInstance or Actor reference.
"""
    },


    {
        "error": "Unable to find package",

        "reason":
        "Unreal Engine cannot locate the referenced asset or package.",

        "solution":
        """
1. Check asset path.
2. Verify the package exists.
3. Check plugin mount point.
4. Rebuild project.
"""
    }
]


def search_ue_error(error_message: str):

    for item in ue_error_db:

        if item["error"].lower() in error_message.lower():

            return item


    return {
        "error": error_message,
        "reason": "No matching UE error found.",
        "solution": "Please provide more information."
    }