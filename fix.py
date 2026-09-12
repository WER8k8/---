import os
files = [
    r"backend\app\api\v1\content.py",
    r"backend\app\api\v1\seo\batch_seo.py",
    r"backend\app\api\v1\seo\dashboard.py",
    r"backend\app\repositories\content_repository.py",
    r"backend\app\services\media_seo_service.py",
    r"backend\app\services\seo_analyzer.py"
]
for file in files:
    try:
        with open(file, 'r', encoding='utf-8') as f:
            c = f.read()
        c = c.replace("`nfrom app.models.seo_metadata import SeoMetadata", "\nfrom app.models.seo_metadata import SeoMetadata")
        c = c.replace("ContentVersion, \nfrom app.models.seo_metadata", "ContentVersion\nfrom app.models.seo_metadata")
        c = c.replace("ContentPage, \nfrom app.models.seo_metadata", "ContentPage\nfrom app.models.seo_metadata")
        with open(file, 'w', encoding='utf-8') as f:
            f.write(c)
    except Exception as e:
        print(f"Error {file}: {e}")
