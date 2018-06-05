#include "db_commit_step_optimizer.h"

DB_Commit_Step_Optimizer::DB_Commit_Step_Optimizer()
{

}
void DB_Commit_Step_Optimizer::timer_start()
{
    elapsed_timer.start();
}

bool DB_Commit_Step_Optimizer::ready_to_commit(unsigned long & num_records_in){

    if(num_records_in > next_record_to_commit)
    {
        num_records = num_records_in;
        return true;
    }
    else
        return false;
}

 void DB_Commit_Step_Optimizer::optimize_step()
 {
     float new_commit_speed = ((float) (num_records - last_record_when_commit)) /
             ((float)   elapsed_timer.elapsed());
     if (commit_speed<0)
     {// initial state
         commit_speed = new_commit_speed;
         new_commit_speed *= 10; // assuming increasing step is better
     }

     if (new_commit_speed > commit_speed)
     { // nice, keep this trend going.
         next_record_to_commit_step_delta += next_record_to_commit_step_delta/3.0f;
     }
     else
     {// bad, reset next_record_to_commit_step_delta to initital value
         if (next_record_to_commit_step_delta>0)
             next_record_to_commit_step_delta = -NEXT_RECORD_TO_COMMIT_STEP_DELTA;
         else
             next_record_to_commit_step_delta = NEXT_RECORD_TO_COMMIT_STEP_DELTA;
     }
     next_record_to_commit_step += next_record_to_commit_step_delta;

     // safe check
     if (next_record_to_commit_step<10){
         qDebug()<< __FILE__<< __LINE__<< __FUNCTION__ << "\n\t"<<"step too small, check here";
         next_record_to_commit_step = 10;
     }

     last_record_when_commit = num_records;
     next_record_to_commit = num_records + next_record_to_commit_step;
//         qDebug()<< __FILE__<< __LINE__<< __FUNCTION__
//                 << "\n\tnext_record_to_commit_step_delta"<<next_record_to_commit_step_delta;
//         qDebug()<<"\n\tnext_record_to_commit_step"<<next_record_to_commit_step;
 }



