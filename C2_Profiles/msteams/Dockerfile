FROM itsafeaturemythic/mythic_python_dotnet:latest

WORKDIR /Mythic/
COPY [".", "."]
RUN pip install -r requirements.txt
CMD ["python3", "main.py"]
