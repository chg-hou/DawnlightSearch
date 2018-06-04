#ifndef DB_COMMIT_STEP_OPTIMIZER_H
#define DB_COMMIT_STEP_OPTIMIZER_H

// TODO: optimize this toy

#include <QElapsedTimer>
#include "globals.h"

#define  NEXT_RECORD_TO_COMMIT_INIT_VALUE       10000L
#define  NEXT_RECORD_TO_COMMIT_STEP_INIT_VALUE  5000L
#define  NEXT_RECORD_TO_COMMIT_STEP_DELTA       2000.0f

class DB_Commit_Step_Optimizer
{
public:
    DB_Commit_Step_Optimizer();

    bool ready_to_commit(unsigned long & num_records);
    void timer_start();
    //  database.commit();
    void optimize_step();

    QElapsedTimer elapsed_timer;

    unsigned long  num_records=0;

    unsigned long  last_record_when_commit = 0;
    unsigned long  next_record_to_commit = NEXT_RECORD_TO_COMMIT_INIT_VALUE;
    long  next_record_to_commit_step = NEXT_RECORD_TO_COMMIT_STEP_INIT_VALUE;
    float next_record_to_commit_step_delta = NEXT_RECORD_TO_COMMIT_STEP_DELTA;
    float commit_speed = -1;
};

#endif // DB_COMMIT_STEP_OPTIMIZER_H
