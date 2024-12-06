# Experiment Resources

There are currently three robots with custom experiment contexts. 

1. Atlas
2. Digit
3. Optimus




## Breakdown of {robot}-resource-file.json

All resource files are structured in a specific way and any new resource files must be created following the template describe below in order for the experiment to properly recognize and run the experiment. 
All resource files are JSON files, which is made up of key-value pairs where each key is a unique identifier (in quotes) and the value can be a variety of types including string, array, object, or boolean.

A sample of the resource file template is as shown:

```json
{
    "subgoal_A": {
        "context": "...",
        "children": [],
        "behavior_library": [
            {
                "id": "...",
                "name": "...",
                "in_behavior_bank": false
            },
            {
                "id": "...",
                "name": "...",
                "in_behavior_bank": true
            }
        ],
        "interruptions": {
        }
    },
    "subgoal_B": {
        "context": "...",
        "children": [],
        "behavior_library": [
            {
                "id": "...",
                "name": "...",
                "in_behavior_bank": false
            },
            {
                "id": "...",
                "name": "...",
                "in_behavior_bank": true
            }
        ],
        "interruptions": {
        }
    },
}
```

The resource-file.json is organized by different subgoals. These subgoals make up the main flow of the experiment behavior tree. Each subgoal has associated context, a behavior library, and interruptions. 

Let's break it down.

### Structure Breakdown

```json
{
    "subgoal_A": { ... },
    "subgoal_B": { ... }
}
```
- The top level keys (subgoal_A, subgoal_B) represent different subgoals. These are unique identifiers for each subgoal.

Each subgoal has the following structure. 

```json
"subgoal_A": {
        "context": "...",
        "children": [],
        "behavior_library": [
            {
                "id": "...",
                "name": "...",
                "in_behavior_bank": false
            },
            {
                "id": "...",
                "name": "...",
                "in_behavior_bank": true
            }
        ],
        "interruptions": {}
    }
```


#### Context
The context is a string paragraph describing the context revolving this specific subgoal. 
Example
``` 
"context": "Atlas is assigned to retrieve medicine A from the medicine cabinet. Atlas is currently on the third floor near the nurse's desk. The medicine cabinet is located in the pharmacy room on the third floor. The medicine cabinet has a total 5 stock for medicine A. To retrieve medicine from the pharmacy room, qualified personnel must communicate with the pharmacist at the door and request the medicine they require.",
```
Note: Both the key ("context") and the value (the paragraph) must be in quotes to properly identify them as strings.

#### Children
The children field represents the children nodes of this subgoal behavior tree. It consists of a list of behavior id's, in the form of strings, that match behaviors listed in the behavior_library field 
The list of behaviors determines the flow of execution by specifying the order of behaviors the robot will follow when it comes to execution time, hence the order of the behaviors matter.

Example
```json
"children": [
            "take_path_to_medicine_cabinet",
            "unlock_cabinet",
            "retrieve_medicine"
        ],
```

In order to place behaviors in the children array, these behaviors must exist in the respective behavior library. 

```json
    "behavior_library": [
        {
            "id": "take_path_to_medicine_cabinet",
            "name": "take acceptable path to the medicine cabinet",
            "in_behavior_bank": false
        },
        {
            "id": "unlock_cabinet",
            "name": "unlock the cabinet"
        },
        {
            "id": "retrieve_medicine",
            "name": "retrieve the medicine"
        },
    ]
```
More about the behavior library below.

#### Behavior Library

```json
    "behavior_library": [
        {
            "id": "take_path_to_medicine_cabinet",
            "name": "take acceptable path to the medicine cabinet",
            "in_behavior_bank": false
        },
        {
            "id": "unlock_cabinet",
            "name": "unlock the cabinet"
        },
        {
            "id": "retrieve_medicine",
            "name": "retrieve the medicine"
        },
        {
            "id": "wait_for_cabinet_access",
            "name": "wait at medicine cabinet until it is accessible",
            "in_behavior_bank": true
        },
        {
            "id": "alert_adminstrator",
            "name": "alert adminstrator for assistance",
            "in_behavior_bank": true
        },
        {
            "id": "request_medicine",
            "name": "request required medicine from pharmacist",
            "in_behavior_bank": true
        }
    ],
```


The behavior library represents an array of all behaviors associated with this subgoal. Introduced above in the children array, some of these behaviors will already be associated with the existing subgoal children list. Again, all behaviors listed in the children must exist in the behavior library.

Each of these behaviors is in the form of an object. They must include the attribute "id" and "name". 

```json
{
    "id": "take_path_to_medicine_cabinet",
    "name": "take acceptable path to the medicine cabinet",
    "in_behavior_bank": false
},
```

Besides the behaviors found in the children list, additional behaviors will also be found in the behavior library. These additional behaviors will form what is called the behavior bank. The behavior bank appears during the experiment when the participant is prompted to add a new behavior to the existing subgoal behavior tree. The possible behaviors to add will come from the behavior bank described here. 
In order for a behavior to be included in the behavior bank, it must be specified with the following attribute

``` "in_behavior_bank": true```

If this attribute is not included or "in_behavior_bank": false, then this behavior will not be one of the options displayed when the participant is prompted to choose a behavior to add to the behavior tree.
