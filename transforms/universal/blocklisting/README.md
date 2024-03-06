# URL Block List Annotator 
Please see the set of
[transform project conventions](../../transform-conventions.md)
for details on general project conventions, transform configuration,
testing and IDE set up.

## Summary 
The block listing annotator/transform maps an input table to an output table
by  using a list of domains that are intended to be blocked 
(i.e. ultimately removed from the tables).
The output table is annotated to include a new column, named 

## Configuration and command line Options

The set of dictionary keys holding [BlockListTransform](src/blocklist_transform.py) 
configuration for values are as follows:

* _bl_annotation_column_name_ - specifies the name of the table column into which the annotation is placed.
This column is **added** to the output tables.  The default is 
* _bl_source_url_column_name_ - specifies the name of the table column holding the URL from which the document was retrieved.
* _bl_blocked_domain_list_path - specifies the directory holding files matching 
the regular expression `domains*`.


## Running
