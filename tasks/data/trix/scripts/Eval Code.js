//! textarea code 'Type code to run'

try {
  eval(op.code);
} catch (err) {
  log(err.toString(), "red");
}
