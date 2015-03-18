/**
 * Created by wang on 15-3-18.
 */

var main = function() {
    db.stage.update({}, {$set: {elite_changed: true}}, {multi: true})
}
