/**
 * Created by wang on 14-9-19.
 */

var _change = function(obj) {
    db.plunder.update({_id: obj._id}, {$unset: {chars: 1, target_char: 1, got_reward: 1}})
}

var main = function() {
    db.plunder.find().forEach(_change);
}
