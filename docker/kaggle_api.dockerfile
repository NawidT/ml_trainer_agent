FROM python:3.9-slim

RUN pip install kaggle \ 
    && mkdir -p /root/.kaggle \
    && chmod 755 /root/.kaggle
# the first command will install kaggle and create the kaggle directory
# the second command will create the kaggle directory
# the third command will set the permissions for the kaggle directory, only the root user can access it

ENTRYPOINT ["bash", "-c", "echo '{\"username\":\"'$KAGGLE_USERNAME'\",\"key\":\"'$KAGGLE_KEY'\"}' > /root/.kaggle/kaggle.json && chmod 600 /root/.kaggle/kaggle.json && exec \"$@\"", "--"]

# this is the original entrypoint
# ENTRYPOINT [
#   "bash", "-c",
#   "echo '{\"username\":\"'$KAGGLE_USERNAME'\",\"key\":\"'$KAGGLE_KEY'\"}' > /root/.kaggle/kaggle.json && \
#    chmod 600 /root/.kaggle/kaggle.json && \
#    exec \"$@\"",
#   "--"
# ]