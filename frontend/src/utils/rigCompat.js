/**
 * Rig compatibility: event.rig_options = minimum required; driver must meet or exceed.
 * Mirrors backend app.utils.rig_compat.driver_rig_satisfies_event.
 */
const WHEEL_ORDER = { legacy: 0, force_feedback_nm: 1 };
const PEDALS_ORDER = { basic: 0, spring: 1, premium: 2 };
const DEFAULT_DRIVER_RIG = { wheel_type: 'legacy', pedals_class: 'basic', manual_with_clutch: false };

export function driverRigSatisfiesEvent(driverRig, eventRig) {
  if (!eventRig || (!eventRig.wheel_type && !eventRig.pedals_class && eventRig.manual_with_clutch == null)) {
    return true;
  }
  const driver = driverRig && (driverRig.wheel_type != null || driverRig.pedals_class != null || driverRig.manual_with_clutch != null)
    ? driverRig
    : DEFAULT_DRIVER_RIG;

  const reqWheel = eventRig.wheel_type;
  if (reqWheel && reqWheel in WHEEL_ORDER) {
    const driverWheel = driver.wheel_type;
    if (driverWheel == null || !(driverWheel in WHEEL_ORDER)) return false;
    if (WHEEL_ORDER[driverWheel] < WHEEL_ORDER[reqWheel]) return false;
  }

  const reqPedals = eventRig.pedals_class;
  if (reqPedals && reqPedals in PEDALS_ORDER) {
    const driverPedals = driver.pedals_class;
    if (driverPedals == null || !(driverPedals in PEDALS_ORDER)) return false;
    if (PEDALS_ORDER[driverPedals] < PEDALS_ORDER[reqPedals]) return false;
  }

  if (eventRig.manual_with_clutch === true && !driver.manual_with_clutch) return false;
  return true;
}
