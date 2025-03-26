FROM python:3.9-slim

COPY requirements.txt .

RUN pip install -r requirements.txt \
    && mkdir -p /root/.kaggle \
    && chmod 755 /root/.kaggle


ENTRYPOINT ["bash", "-c", "echo '{\"username\":\"'$KAGGLE_USERNAME'\",\"key\":\"'$KAGGLE_KEY'\"}' > /root/.kaggle/kaggle.json && chmod 600 /root/.kaggle/kaggle.json && exec \"$@\"", "--"]

# this is the original entrypoint
# ENTRYPOINT [
#   "bash", "-c",
#   "echo '{\"username\":\"'$KAGGLE_USERNAME'\",\"key\":\"'$KAGGLE_KEY'\"}' > /root/.kaggle/kaggle.json && \
#    chmod 600 /root/.kaggle/kaggle.json && \
#    exec \"$@\"",
#   "--"
# ]