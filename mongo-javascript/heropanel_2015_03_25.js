/**
 * Created by wang on 15-3-18.
 */

var main = function() {
    db.heropanel.update({}, {$set: {has_opened: true}}, {multi: true});
}
