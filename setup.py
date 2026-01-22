# setup.py
from setuptools import setup, find_packages
import os
import glob
from pathlib import Path

# Đọc README an toàn (nếu có), dùng fallback khi không tồn tại
root = Path(__file__).resolve().parent
readme_path = root / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")
else:
    long_description = "SkillNer fork - Custom skill and job title extraction using spaCy"

# Gom tất cả file JSON trong thư mục data (SkillNER/data)
data_dir = root / "data"
data_files = []
if data_dir.exists():
    data_files = [str(p) for p in data_dir.glob("*.json")]

setup(
    name="skillner-custom",
    version="0.2.0",
    author="Trần Đại Tài",
    author_email="trandaitai2005@gmail.com",
    description="SkillNer fork - Custom skill and job title extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TranDaiTai/SkillNER-fork",
    project_urls={
        "Bug Tracker": "https://github.com/TranDaiTai/SkillNER-fork/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*", "examples*"]),
    include_package_data=True,
    # Nếu bạn muốn các file JSON trong SkillNER/data được cài đặt cùng package,
    # chúng ta liệt kê chúng trong `data_files`. Lưu ý: `data_files` sẽ cài
    # các file này vào một location bên ngoài package (ví dụ site-packages/skillner_data).
    # Nếu muốn package có thể truy cập trực tiếp từ import, cân nhắc di chuyển
    # thư mục `data/` vào trong package `skillNer/`.
    data_files=[("skillner_data", data_files)] if data_files else [],
    install_requires=[
        "spacy>=3.0",
        "nltk",
        "jellyfish",
        "numpy",
        "scipy",
        "pandas",
    ],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "pytest",
        ],
    },
    entry_points={
        # Nếu muốn CLI, bật phần bên dưới và tạo module skillNer.cli:main
        # "console_scripts": [
        #     "skillner-extract = skillNer.cli:main",
        # ],
    },
    keywords="skill extraction, ner, spacy, job title extraction",
    license="MIT",
)