<?php

use Puneetxp\CompilePhp\setup;

// use Puneetxp\CompilePhp\Compile\compilephp;
require "./vendor/autoload.php";
// require_once __DIR__ . '/setup/autosetup.php';
$setup = new setup(__DIR__);
$setup->config();
// (new compilephp("Resource/View",__DIR__))->run();
//(new mysqltable())->migrate();
// (new setup(__DIR__))->table_set()->php_set()->deno_set()->angular_set()->write();