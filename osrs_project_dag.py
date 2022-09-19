import datetime
from airflow.operators.python_operator import PythonOperator
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow.providers.amazon.aws.operators.ec2 import EC2StartInstanceOperator
from airflow.providers.amazon.aws.operators.ec2 import EC2StopInstanceOperator
from airflow import DAG
import time







with DAG(
    'ec2sshdag',
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
    default_args={
        'depends_on_past': False,
        'email': ['XXXX@email.com'],
        'email_on_failure': True,
        'email_on_retry': True,
        'retries': 1,
        'retry_delay': datetime.timedelta(minutes=5),
        # 'queue': 'bash_queue',
        # 'pool': 'backfill',
        # 'priority_weight': 10,
        # 'end_date': datetime(2016, 1, 1),
        # 'wait_for_downstream': False,
        # 'sla': timedelta(hours=2),
        # 'execution_timeout': timedelta(seconds=300),
        # 'on_failure_callback': some_function,
        # 'on_success_callback': some_other_function,
        # 'on_retry_callback': another_function,
        # 'sla_miss_callback': yet_another_function,
        # 'trigger_rule': 'all_success'
    },
    description='EC2 SSH DAG',
    schedule_interval=datetime.timedelta(days=1),
    start_date=datetime.datetime(2022, 9, 16),
    catchup=False
) as dag:

    def wait_task():
        time.sleep(300)




    t1 = EC2StartInstanceOperator(task_id="first_task",     
     instance_id="EC2 INSTANCE ID",                     ## If EC2 is already running,
     aws_conn_id="aws_default",                         ## this will just verify
     region_name="AWS REGION OF EC2 INSTANCE", 
     check_interval=15,
     dag=dag)

                                                        ## "aws_default" and "ec2ssh"
                                                        ## connections must be configured
    t2 = SSHOperator(                                   ## in Airflow UI
     ssh_conn_id="ec2ssh",
     task_id="second_task",
     depends_on_past=True,
     command="cd PROJECTFOLDER;python3 Extract_and_Load_Raw.py",  ## Run 1st python script
     dag=dag)


    t3 = PythonOperator(
     task_id="third_task"
     python_callable=wait_task,                 ## Give time for scheduled
     depends_on_past=True,                      ## queries to run
     dag=dag
    )

    
    t4 = SSHOperator(     
     ssh_conn_id="ec2ssh",
     task_id="fourth_task",
     depends_on_past=True,
     command="cd PROJECTFOLDER;python3 Send_Output.py",   ## Run 2nd python script
     dag=dag)





    # t4 = EC2StopInstanceOperator(task_id="fourth_task",
    #  instance_id="YOUR EC2 INSTANCE ID",
    #  aws_conn_id='aws_default',
    #  region_name="AWS REGION OF EC2 INSTANCE",
    #  check_interval=15,
    #  dag=dag)

    # Optional EC2StopInstanceOperator. I am using a free tier EC2 instance
    # which is free for continuous use, but with AWS elastic IP which is 
    # only free when tied to running instances


    t1 >> t2 >> t3 >> t4





